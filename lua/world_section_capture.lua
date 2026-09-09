-- Read-only World 2.4 section-definition -> allocated-object placement evidence.
-- This does not run a future section, allocate objects or change loader progress.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 section capture only')
local first=tonumber(os.getenv('CRUISN_SECTION_FIRST') or '5900')
local last=tonumber(os.getenv('CRUISN_SECTION_LAST') or '6020')
local binding_mode=os.getenv('CRUISN_SECTION_BINDINGS') or '0'
assert(binding_mode=='0' or binding_mode=='1','invalid section binding trace mode')
local final_mode=os.getenv('CRUISN_SECTION_FINAL') or '0'
assert(final_mode=='0' or final_mode=='1','invalid final section trace mode')
assert(final_mode=='0' or binding_mode=='1','final section trace requires material bindings')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=12000,'invalid bounded section interval')
local frame,taps,out,current,failure,serial,collecting=0,{},nil,nil,nil,0,false
local bindings,preallocation=nil,nil
local final_out,finishing=nil,nil
local function words(p,n)
    assert(p>=0 and n>=0 and n<=64 and (p+n<=0x20000
        or p>=0x809800 and p+n<=0x80a000 or p>=0xc00000 and p+n<=0x1000000),
        'section source span is outside mapped RAM/ROM')
    local a={};for i=0,n-1 do a[#a+1]=s:read_u32(p+i) end;return a
end
local function emit(r,stream)
    local keys={};for k in pairs(r) do keys[#keys+1]=k end;table.sort(keys)
    local parts={};for _,k in ipairs(keys) do
        local v=type(r[k])=='table' and '['..table.concat(r[k],',')..']' or tostring(r[k])
        parts[#parts+1]='"'..k..'":'..v
    end
    (stream or out):write('{'..table.concat(parts,',')..'}\n')
end
local function guarded(fn)
    return function(...)
        -- The diagnostic globals include D580 itself. Suppress callbacks from
        -- our own reads so they cannot be mistaken for another guest allocation.
        if failure or collecting then return end
        collecting=true
        local ok,err=pcall(fn,...)
        collecting=false
        if not ok then failure=tostring(err) end
    end
end
local function close()
    for _,tap in ipairs(taps) do tap:remove() end;taps={}
    if out then out:close();out=nil end
    if bindings then bindings:close();bindings=nil end
    if final_out then final_out:close();final_out=nil end
end
cruisn_section_stop=emu.add_machine_stop_notifier(close)
return function(n)
    if failure then error(failure) end
    frame=n
    if n==first then
        local code={[0x7b9a]=0x084a2501,[0x7b9b]=0x6200625c,[0x7b9d]=0x0820d580,
          [0x7ba5]=0x0820d57d,[0x7bc7]=0x08227c58,[0x7bdc]=0x62009045,
          [0x7bdd]=0x08412501,[0x7c1b]=0x0821d58d,[0x7cdd]=0x0828d575,
          [0x7ce2]=0x1528d575,[0x90cb]=0x24e02122,[0x90db]=0xc00201c1}
        if binding_mode=='1' then
            code[0x6263]=0x08400a02;code[0x6265]=0x15400010
            code[0x6266]=0x08400a01;code[0x6268]=0x15400011
            code[0x9500]=0x022a4151;code[0x9501]=0x0840c200
        end
        if final_mode=='1' then
            code[0x7bef]=0x0e200000;code[0x7bf0]=0x03e0ffec;code[0x7bf2]=0x620094fe
            code[0x7bf3]=0x6a070001;code[0x7bf4]=0x15400410;code[0x7c4e]=0x0820d5a3
        end
        for p,v in pairs(code) do assert(s:read_u32(p)==v,string.format('section signature %x',p)) end
        out=assert(io.open('world-section-placement.jsonl','w'))
        if final_mode=='1' then
            final_out=assert(io.open('world-section-final.jsonl','w'))
            taps[#taps+1]=s:install_read_tap(0xd5a3,0xd5a3,'section_object_final',guarded(function(o,d,m)
                if cpu.state.PC.value~=0x7c4f then return end
                assert(finishing and finishing.object==cpu.state.AR4.value,'final section object owner mismatch')
                finishing.final=words(finishing.object,28);finishing.final_frame=frame
                emit(finishing,final_out);finishing=nil
            end))
        end
        if binding_mode=='1' then
            bindings=assert(io.open('world-section-bindings.jsonl','w'))
            -- Capture the model argument BEFORE 7B9B calls the allocator.
            -- The ordinary placement boundary at 7B9D is after its initial
            -- texture/palette setup and can only see subsequent overrides.
            taps[#taps+1]=s:install_read_tap(0xc00000,0xffffff,'section_allocator_argument',guarded(function(o,d,m)
                if cpu.state.PC.value~=0x7b9b then return end
                assert(not current and not preallocation,'unfinished allocator request')
                local ids=words(d-2,2)
                local palette=s:read_u32(0x4151);local texture=s:read_u32(0x4150)
                assert(palette<0x20000 and texture<0x20000,'binding table is outside main RAM')
                local pv=words((palette+ids[1])&0xffffffff,1)[1]
                local tv=words((texture+ids[2])&0xffffffff,1)[1]
                preallocation={serial=serial+1,frame=frame,source=o,model=d,
                    resources={ids[1],ids[2],palette,texture,pv,tv}}
            end))
            taps[#taps+1]=s:install_write_tap(0x1000,0x1ffff,'section_material_binding',guarded(function(o,d,m)
                local owner=current or preallocation
                if not owner then return end
                local pc=cpu.state.PC.value
                -- 625C returns the new object in AR0; 7B9C copies it to AR4
                -- only AFTER the two initial binding writes. Later overrides
                -- use AR4. Guard both actual store instructions above.
                if not current and pc~=0x6266 and pc~=0x6269 then return end
                local object=current and current.object or cpu.state.AR0.value
                if not current then assert(cpu.state.AR2.value==owner.model,'allocator model owner changed') end
                if o~=object+16 and o~=object+17 then return end
                assert(object>=0x1000 and object<=0x20000-28,'invalid binding object')
                if not owner.initial then owner.initial=words(object,28);owner.binding_object=object end
                local registers,sources={},{}
                for i=0,7 do
                    local p=cpu.state['AR'..i].value
                    registers[#registers+1]=p
                    local start=p-4
                    if start>=0 and (start+8<=0x20000 or start>=0x809800 and start+8<=0x80a000
                        or start>=0xc00000 and start+8<=0x1000000) then
                        sources[#sources+1]=i;sources[#sources+1]=start
                        for _,v in ipairs(words(start,8)) do sources[#sources+1]=v end
                    end
                end
                emit({serial=owner.serial,frame=frame,object=object,field=o-object,phase=current and 1 or 0,
                    pc=pc,value=d,mask=m,registers=registers,sources=sources,code=words(pc-3,6)},bindings)
            end))
        end
        taps[#taps+1]=s:install_read_tap(0xd580,0xd580,'section_object_begin',guarded(function(o,d,m)
            if cpu.state.PC.value~=0x7b9e then return end
            assert(not current and not finishing,'unfinished section allocation')
            serial=serial+1
            local object=cpu.state.AR4.value;local source=cpu.state.AR5.value-1
            local section=cpu.state.AR7.value
            local definition=words(source,6)
            assert(object>=0x1000 and object<=0x20000-28,'invalid allocated object')
            assert(definition[1]==s:read_u32(object+13),'source model differs from allocated model')
            current={serial=serial,frame=frame,emulator_frame=manager.machine.screens[':screen']:frame_number(),
              object=object,source=source,definition=definition,section_pointer=section,section_words=words(section,12),
              section_tag=d,section_flags=s:read_u32(0xd57d),heading=s:read_u32(0xd57e),
              matrix=words(s:read_u32(0x7c58),9),loader=words(0xd575,17),trig_constants=words(0xcc35,7)}
            if bindings then
                assert(preallocation and preallocation.serial==serial and preallocation.source==source
                    and preallocation.model==definition[1],'allocator argument owner mismatch')
                assert(not preallocation.binding_object or preallocation.binding_object==object,'allocator binding owner changed')
                current.initial=preallocation.initial or words(object,28)
                current.binding_first_frame=preallocation.frame;current.binding_scope=3
                current.binding_resources=preallocation.resources
                preallocation=nil
            end
        end))
        taps[#taps+1]=s:install_read_tap(0xd58d,0xd58d,'section_object_ready',guarded(function(o,d,m)
            if cpu.state.PC.value~=0x7c1c then return end
            assert(current and current.object==cpu.state.AR4.value,'section object owner mismatch')
            current.actual=words(current.object,28);current.end_frame=frame
            if final_out then
                local metadata=current.definition[6]
                local signed=metadata>=0x80000000 and metadata-0x100000000 or metadata
                local index=math.floor(signed/0x100000)
                current.override_index=index;current.override_lookup=-1
                if index>=0 then
                    local table=s:read_u32(0x4151)
                    assert(table<0x20000 and table+index<0x20000,'override table span is outside main RAM')
                    current.override_lookup=words(table+index,1)[1]
                end
                current.loader_special=d
                finishing=current
            end
            emit(current);current=nil
        end))
    end
    if n==last+1 then assert(not current and not preallocation and not finishing,'incomplete section object at interval end');close() end
end
