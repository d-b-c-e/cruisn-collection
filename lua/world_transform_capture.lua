-- Read-only World 2.4 model/transform oracle inputs and actual projected vertices.
-- No guest writes or activation changes. Every tap failure reaches session.lua.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 transform capture only')
local first=tonumber(os.getenv('CRUISN_TRANSFORM_FIRST') or '5900')
local last=tonumber(os.getenv('CRUISN_TRANSFORM_LAST') or '5910')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=120,'invalid bounded transform interval')
local frame,serial,current,error_message=0,0,nil,nil
local taps,out,draws,future={},nil,nil,nil
local pending,page={},0
local counts={starts=0,projected=0,draws=0,unmatched_draws=0,pending=0}
local function words(address,count)
    assert(address>=0 and count>=0 and count<=4096 and address+count<=0x1000000,'invalid memory span')
    local v={};for i=0,count-1 do v[#v+1]=s:read_u32(address+i) end;return v
end
local function array(v) return '['..table.concat(v,',')..']' end
local function emit(v,stream)
    local keys={};for k in pairs(v) do keys[#keys+1]=k end;table.sort(keys)
    local items={}
    for _,k in ipairs(keys) do
        local value=type(v[k])=='table' and array(v[k]) or tostring(v[k])
        items[#items+1]='"'..k..'":'..value
    end
    (stream or out):write('{'..table.concat(items,',')..'}\n')
end
local function guarded(fn)
    return function(...)
        if error_message then return end
        local ok,reason=pcall(fn,...)
        if not ok then error_message=tostring(reason) end
    end
end
local function close()
    for _,tap in ipairs(taps) do tap:remove() end;taps={}
    if out then out:close();out=nil;draws:close();draws=nil;future:close();future=nil end
end
cruisn_transform_stop=emu.add_machine_stop_notifier(close)
return function(n)
    if error_message then error(error_message) end
    frame=n
    if n==first then
        local expected={
            [0x7d]=0x082a0041,[0x7f]=0x082d0043,[0x81]=0x26e32322,
            [0x90]=0x14420601,[0x9c]=0x1529d4bf,[0xa0]=0x04a30040,
            [0xed]=0x082b0049,[0x199]=0x04f21387,[0x19f]=0x24c00182,
            [0x21b]=0x24c00182,[0x241]=0x082ed4bf,[0x2e0]=0x082ed4bf,
            [0x69]=0x082861ee,[0x7b55]=0x082861ec,[0x7b5c]=0x1ae03000}
        for address,value in pairs(expected) do
            assert(s:read_u32(address)==value,string.format('transform signature mismatch at %x',address))
        end
        out=assert(io.open('world-transform.jsonl','w'))
        future=assert(io.open('world-pending-models.jsonl','w'))
        draws=assert(io.open('world-transform-draws.csv','w'))
        draws:write('frame,call,object,model,pc,page,flags,palette,x0,y0,x1,y1,x2,y2,x3,y3,uv0,uv1,uv2,uv3,texture,word15\n')
        page=s:read_u32(0x980040)
        local table_base=s:read_u32(0x4d)
        local reciprocal=assert(io.open('world-transform-reciprocals.bin','wb'))
        for i=-80,4999 do reciprocal:write(string.pack('<I4',s:read_u32(table_base+i))) end
        reciprocal:close()
        -- Pending list is a separate linked list, not a model allowlist. Snapshot
        -- at the scene boundary after the shared billboard/camera setup.
        taps[#taps+1]=s:install_read_tap(0x61ee,0x61ee,'host_pending_scene',guarded(function(o,d,m)
            if cpu.state.PC.value~=0x6a then return end
            local head=s:read_u32(0x61ec)
            local id=s:read_u32(head);local seen={};local size=0
            local camera=words(s:read_u32(0x41),3);local view=words(s:read_u32(0x43),9)
            local billboard=words(s:read_u32(0x48),9)
            local origin=words(s:read_u32(0x47)+2,2)
            while id~=0 do
                assert(id>=0x1000 and id+32<=0x20000 and not seen[id],'invalid/cyclic pending list')
                seen[id]=true;size=size+1;assert(size<=2048,'pending list exceeded bound')
                local obj=words(id,32);local base=obj[14];local flags=obj[15]
                local lods={base}
                if flags&0x200~=0 then
                    lods[#lods+1]=s:read_u32(base-3)
                    if flags&4~=0 then lods[#lods+1]=s:read_u32(base-4) end
                end
                for lod,model in ipairs(lods) do
                    local entry={frame=frame,object=id,object_words=obj,model=model,lod=lod-1,
                        camera=camera,view=view,billboard=billboard,origin=origin,page=page,
                        pending_threshold=s:read_u32(0xd584)}
                    -- Alternate geometry codecs are retained as explicit exclusions.
                    if flags&0x861==0 and model>=0x1000 and model+3<0x1000000 then
                        local h=words(model,3);local header=h[3]
                        local pairs=(header&0x300)~=0 and ((header>>10)&255)+1 or 0
                        local input=(header&255)+pairs;local verts=(header&255)+2*pairs
                        local polys=(header>>18)+1
                        assert(verts>0 and verts<=256 and polys<=1024,'unsupported pending model counts')
                        entry.model_words=words(model,3+input*2+polys*2)
                        entry.material_words=words(h[2],polys*3)
                        entry.vertices=verts;entry.input_vertices=input;entry.polygons=polys
                    end
                    emit(entry,future);counts.pending=counts.pending+1
                end
                id=obj[1]
            end
        end))
        taps[#taps+1]=s:install_read_tap(0x40,0x40,'host_transform_owner',guarded(function(o,d,m)
            if cpu.state.PC.value==0xa1 then current=nil end
        end))
        taps[#taps+1]=s:install_read_tap(0x49,0x49,'host_transform_begin',guarded(function(o,d,m)
            if cpu.state.PC.value~=0xee then return end
            local id=cpu.state.AR0.value
            assert(id>=0x1000 and id+32<=0x20000,string.format('object outside work RAM: %x',id))
            local model=s:read_u32(0xd4bf);local head=words(model,3)
            local header=head[3]
            local special=(header&0x300)~=0 and ((header>>10)&0xff)+1 or 0
            local input_vertices=(header&0xff)+special
            local vertices=(header&0xff)+2*special
            local polygons=(header>>18)+1
            assert(vertices>0 and vertices<=256 and polygons<=1024,'unsupported model count')
            assert(cpu.state.AR1.value==model+3,'unexpected model vertex start')
            serial=serial+1;counts.starts=counts.starts+1
            local camera=words(s:read_u32(0x41),3)
            local view=words(s:read_u32(0x43),9)
            local relative=words(cpu.state.AR6.value-1,5)
            current={frame=frame,call=serial,object=id,model=model,vertex_buffer=d,
                object_words=words(id,32),camera=camera,view=view,
                matrix=words(cpu.state.AR5.value,9),matrix_address=cpu.state.AR5.value,
                camera_space=relative,vertices=vertices,input_vertices=input_vertices,polygons=polygons,
                fast=s:read_u32(0xd4be),
                model_words=words(model,3+input_vertices*2+polygons*2),
                material_words=words(head[2],polygons*3)}
        end))
        taps[#taps+1]=s:install_read_tap(0xd4bf,0xd4bf,'host_transform_projected',guarded(function(o,d,m)
            local pc=cpu.state.PC.value
            if pc~=0x242 and pc~=0x2e1 then return end
            if not current then return end
            assert(current.model==d,'model changed during projection')
            local id=pc==0x2e1 and s:read_u32(cpu.state.SP.value) or cpu.state.AR0.value
            assert(current.object==id,'object changed during projection')
            assert(not current.projected,'duplicate completed projection')
            current.projected=words(current.vertex_buffer,current.vertices*3)
            current.end_frame=frame;current.end_pc=pc;current.page=page
            emit(current);counts.projected=counts.projected+1
        end))
        taps[#taps+1]=s:install_write_tap(0x980040,0x980040,'host_transform_page',guarded(function(o,d,m) page=d end))
        taps[#taps+1]=s:install_write_tap(0x600000,0x600000,'host_transform_dma',guarded(function(o,d,m)
            if #pending<16 then pending[#pending+1]=d&0xffff end
        end))
        taps[#taps+1]=s:install_read_tap(0x980083,0x980083,'host_transform_draw',guarded(function(o,d,m)
            local pc=cpu.state.PC.value
            if #pending>=15 and (pc==0x289 or pc==0x2ca or pc==0x333) then
                local id=pc==0x333 and s:read_u32(cpu.state.SP.value) or cpu.state.AR0.value
                local owner=current and current.object==id and current.projected and current or nil
                draws:write(string.format('%d,%d,%d,%d,%d,%d',frame,owner and owner.call or 0,id,
                    owner and owner.model or 0,pc,page))
                for i=1,16 do draws:write(','..(pending[i] or 0)) end
                draws:write('\n');counts.draws=counts.draws+1
                if not owner then counts.unmatched_draws=counts.unmatched_draws+1 end
            end
            pending={}
        end))
    elseif n==last+1 then
        close()
        assert(counts.projected>0 and counts.draws>0,'no actual transform/draw evidence')
        local f=assert(io.open('world-transform-summary.json','w'))
        f:write(string.format('{"first":%d,"last":%d,"starts":%d,"projected":%d,"draws":%d,"unmatched_draws":%d,"pending":%d}\n',
            first,last,counts.starts,counts.projected,counts.draws,counts.unmatched_draws,counts.pending));f:close()
    end
end
