-- MUTATING diagnostic: test the World 2.4 pending-list lookahead itself.
-- Covers every pending object, not just verified mountain models. No production
-- recommendation is implied. The guest transfers objects, which remain active
-- after the bounded tap closes. Original projection/far checks remain unchanged.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 pending-list diagnostic only')
assert(os.getenv('MIDV_SCENERY_LEAD')=='0','disable selective native activation for this comparison')
local first=tonumber(os.getenv('CRUISN_PENDING_FIRST') or '5900')
local last=tonumber(os.getenv('CRUISN_PENDING_LAST') or '6140')
local lead=tonumber(os.getenv('CRUISN_PENDING_LEAD') or '8')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=240 and lead and lead%1==0 and lead>=0 and lead<=8,
    'invalid bounded pending-list experiment')
local frame,taps,out,reads=0,{},nil,0
local function close()
    for _,t in ipairs(taps) do t:remove() end;taps={}
    if out then out:close();out=nil end
end
cruisn_pending_distance_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==first then
        assert(s:read_u32(0x7b50)==0x0224d58c and s:read_u32(0x7b51)==0x04a4d584
            and s:read_u32(0x7b58)==0x04800004 and s:read_u32(0x7b5c)==0x1ae03000
            and s:read_u32(0x7b68)==0x0840001b and s:read_u32(0xd58c)==11,
            'World pending-list signature mismatch')
        out=assert(io.open('pending-activation.csv','w'))
        out:write('frame,object,model,flags,radius,section,threshold,earlier\n')
        table.insert(taps,s:install_read_tap(0xd58c,0xd58c,'pending_lookahead',function(o,d,m)
            if cpu.state.PC.value~=0x7b51 then return end
            assert(d==11,'pending lookahead changed during experiment')
            reads=reads+1
            return d+lead
        end))
        table.insert(taps,s:install_write_tap(0x10800,0x1ffff,'pending_transfers',function(o,d,m)
            if cpu.state.PC.value~=0x7b5e then return end
            local object=cpu.state.AR0.value
            if object<0x10800 or object>=0x20000-27 or o~=object+14 then return end
            -- The only Lua read tap covers D58C; these reads cannot re-enter it.
            local model=s:read_u32(object+13)
            local radius=s:read_u32(object+19)
            local section=s:read_u32(object+27)&0xffff
            local threshold=cpu.state.R4.value
            out:write(string.format('%d,%x,%x,%x,%d,%d,%d,%d\n',frame,object,model,d,
                radius,section,threshold,section>threshold-lead and 1 or 0))
        end))
    elseif n==last+1 then
        close();assert(reads>0,'pending-list comparison was not observed')
    end
end
