-- Bounded World 2.4 experiment: activate only four attributed small tree cards.
-- The guest performs its normal pending-list transfer. No RAM writes by this
-- hook; activation persists after the bounded read tap closes.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 tree diagnostic only')
local first=tonumber(os.getenv('CRUISN_TREE_FIRST') or '5900')
local last=tonumber(os.getenv('CRUISN_TREE_LAST') or '6140')
local lead=tonumber(os.getenv('CRUISN_TREE_LEAD') or '8')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=240 and lead and lead%1==0 and lead>=1 and lead<=8,
    'invalid bounded tree activation experiment')
local radii={[0xca57f3]=1950,[0xca5833]=1950,[0xca5863]=818,[0xca5896]=1252}
local frame,tap,out,changed,busy=0,nil,nil,0,false
local function close()
    if tap then tap:remove();tap=nil end
    if out then out:close();out=nil end
end
cruisn_tree_activation_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==first then
        assert(s:read_u32(0x7b50)==0x0224d58c and s:read_u32(0x7b58)==0x04800004
            and s:read_u32(0x7b59)==0x6a290008 and s:read_u32(0x7b5c)==0x1ae03000
            and s:read_u32(0x7b5d)==0x1540000e and s:read_u32(0x7b61)==0x1541c000
            and s:read_u32(0x7b62)==0x1528d50b and s:read_u32(0x7b68)==0x0840001b
            and s:read_u32(0x7b69)==0x02e0ffff and s:read_u32(0xd58c)==11,
            'World pending-list signature mismatch')
        out=assert(io.open('tree-activation.csv','w'))
        out:write('frame,object,model,section,threshold,returned_section\n')
        tap=s:install_read_tap(0x10800,0x1ffff,'pending_tree_activation',function(o,d,m)
            if busy or cpu.state.PC.value~=0x7b69 then return end
            local object=cpu.state.AR0.value
            if object<0x10800 or object>=0x20000-27 or o~=object+27 then return end
            -- PC remains 7B69 during nested object-field reads. Reject reentry
            -- explicitly; field offsets also differ from the section read.
            busy=true
            local model=s:read_u32(object+13)
            local actual_radius=s:read_u32(object+19)
            local flags=s:read_u32(object+14)
            busy=false
            local radius=radii[model]
            if not radius or actual_radius~=radius or flags&0x7fffffff~=0x2008 then return end
            local section=d&0xffff;local threshold=cpu.state.R4.value
            if threshold>0xffff or section<=threshold or section<lead
                or section-lead>threshold then return end
            changed=changed+1
            out:write(string.format('%d,%x,%x,%d,%d,%d\n',frame,object,model,
                section,threshold,section-lead))
            return (d&0xffff0000)|(section-lead)
        end)
    elseif n==last+1 then close();assert(changed>0,'no matching tree activated earlier') end
end
