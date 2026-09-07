local m=(function()
-- Read-only, bounded World camera and actual ADC-read timeline. Camera state is
-- a route-divergence detector, not a claim that these words are vehicle physics.
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24' or manager.machine.system.name=='crusnwld')
local first=tonumber(os.getenv('CRUISN_MOTION_FIRST') or '5880')
local last=tonumber(os.getenv('CRUISN_MOTION_LAST') or '6300')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=12000,'invalid motion trace interval')
local frame,taps,out,adc=0,{},nil,nil
local function close()
    for _,t in ipairs(taps) do t:remove() end
    taps={}
    if out then out:close();adc:close();out=nil end
end
cruisn_world_motion_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==first then
        assert(s:read_u32(0x7d)==0x082a0041 and s:read_u32(0x7f)==0x082d0043,'camera path signature')
        out=assert(io.open('world-camera.csv','w'))
        out:write('frame,x,y,z,m0,m1,m2,m3,m4,m5,m6,m7,m8\n')
        adc=assert(io.open('world-adc.csv','w'));adc:write('frame,time,pc,value\n')
        table.insert(taps,s:install_read_tap(0x993000,0x993000,'world_actual_adc',function(o,d,m)
            adc:write(string.format('%d,%.12f,%x,%x\n',frame,emu.time(),cpu.state.PC.value,d))
        end))
    end
    if out and n<=last then
        local p=s:read_u32(0x41);local m=s:read_u32(0x43)
        assert(p<0x20000 and m>=0x809800 and m<0x809ff8,'camera pointers outside expected RAM')
        out:write(n)
        for i=0,2 do out:write(string.format(',%08x',s:read_u32(p+i))) end
        for i=0,8 do out:write(string.format(',%08x',s:read_u32(m+i))) end
        out:write('\n')
    end
    if n==last+1 then close() end
end

end)()
local a=(function()
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

end)()
return function(n) m(n);a(n) end
