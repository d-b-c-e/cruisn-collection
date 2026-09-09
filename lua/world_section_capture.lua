-- Read-only World 2.4 section-definition -> allocated-object placement evidence.
-- This does not run a future section, allocate objects or change loader progress.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 section capture only')
local first=tonumber(os.getenv('CRUISN_SECTION_FIRST') or '5900')
local last=tonumber(os.getenv('CRUISN_SECTION_LAST') or '6020')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=12000,'invalid bounded section interval')
local frame,taps,out,current,failure,serial,collecting=0,{},nil,nil,nil,0,false
local function words(p,n)
    assert(p>=0 and n>=0 and n<=64 and (p+n<=0x20000
        or p>=0x809800 and p+n<=0x80a000 or p>=0xc00000 and p+n<=0x1000000),
        'section source span is outside mapped RAM/ROM')
    local a={};for i=0,n-1 do a[#a+1]=s:read_u32(p+i) end;return a
end
local function emit(r)
    local keys={};for k in pairs(r) do keys[#keys+1]=k end;table.sort(keys)
    local parts={};for _,k in ipairs(keys) do
        local v=type(r[k])=='table' and '['..table.concat(r[k],',')..']' or tostring(r[k])
        parts[#parts+1]='"'..k..'":'..v
    end
    out:write('{'..table.concat(parts,',')..'}\n')
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
        for p,v in pairs(code) do assert(s:read_u32(p)==v,string.format('section signature %x',p)) end
        out=assert(io.open('world-section-placement.jsonl','w'))
        taps[#taps+1]=s:install_read_tap(0xd580,0xd580,'section_object_begin',guarded(function(o,d,m)
            if cpu.state.PC.value~=0x7b9e then return end
            assert(not current,'unfinished section allocation')
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
        end))
        taps[#taps+1]=s:install_read_tap(0xd58d,0xd58d,'section_object_ready',guarded(function(o,d,m)
            if cpu.state.PC.value~=0x7c1c then return end
            assert(current and current.object==cpu.state.AR4.value,'section object owner mismatch')
            current.actual=words(current.object,28);current.end_frame=frame
            emit(current);current=nil
        end))
    end
    if n==last+1 then assert(not current,'incomplete section object at interval end');close() end
end
