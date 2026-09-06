-- Bounded read-only World 2.4 admission -> submitted polygon provenance.
-- Join only object IDs seen at the far gate in this frame, never a stale model.
local cpu=manager.machine.devices[':maincpu']; local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24', 'World 2.4 provenance only')
local first=tonumber(os.getenv('CRUISN_SCENERY_FIRST') or '1998')
local last=tonumber(os.getenv('CRUISN_SCENERY_LAST') or '2040')
assert(first and last and first%1==0 and last%1==0 and first>=1
    and last>=first and last-first<=240, 'invalid bounded scenery interval')
local frame,page,pending,taps,admitted=0,0,{},{},{}
local draws,objects,count=nil,nil,0
local function signed(n) return n>=0x80000000 and n-0x100000000 or n end
local function close()
    for _,t in ipairs(taps) do t:remove() end; taps={}
    if draws then draws:close();draws=nil end
    if objects then objects:close();objects=nil end
end
cruisn_scenery_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n; admitted={}
    if n==first then
        assert(s:read_u32(0xa0)==0x04a30040 and s:read_u32(0x9c)>>16==0x1529,
            'World object path signature mismatch')
        local selected=s:read_u32(0x9c)&0xffff
        draws=assert(io.open('scenery-draws.csv','w'))
        objects=assert(io.open('scenery-objects.csv','w'))
        draws:write('frame,pc,page,object,model,matched,flags,palette,x0,y0,x1,y1,x2,y2,x3,y3,uv0,uv1,uv2,uv3,texture,word15\n')
        objects:write('frame,object,model,object_flags,depth_minus_radius,radius,far_limit\n')
        page=s:read_u32(0x980040)
        table.insert(taps,s:install_read_tap(0x40,0x40,'scenery_admission',function(o,d,m)
            if cpu.state.PC.value~=0xa1 then return end
            local id=cpu.state.AR0.value
            local model=s:read_u32(selected)
            admitted[id]=model
            objects:write(string.format('%d,%x,%x,%x,%d,%d,%d\n',frame,id,model,
                s:read_u32(id+14),signed(cpu.state.R3.value),signed(cpu.state.R4.value),d))
        end))
        table.insert(taps,s:install_write_tap(0x980040,0x980040,'scenery_page',function(o,d,m) page=d end))
        table.insert(taps,s:install_write_tap(0x600000,0x600000,'scenery_words',function(o,d,m)
            if #pending<16 then table.insert(pending,d&0xffff) end
        end))
        table.insert(taps,s:install_read_tap(0x980083,0x980083,'scenery_trigger',function(o,d,m)
            if #pending>=15 then
                local pc=cpu.state.PC.value
                -- Verified World slow polygon path pushes AR0 onto its stack.
                local id=pc==0x333 and s:read_u32(cpu.state.SP.value) or cpu.state.AR0.value
                local model=admitted[id]
                draws:write(string.format('%d,%x,%d,%x,%x,%d',frame,pc,page,id,model or 0,model and 1 or 0))
                for i=1,16 do draws:write(','..(pending[i] or 0)) end
                draws:write('\n'); count=count+1
            end
            pending={}
        end))
    elseif n==last+1 then close(); assert(count>0,'no scenery submissions captured') end
end
