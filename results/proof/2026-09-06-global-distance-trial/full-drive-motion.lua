-- Read-only, bounded World camera and actual ADC-read timeline. Camera state is
-- a route-divergence detector, not a claim that these words are vehicle physics.
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24' or manager.machine.system.name=='crusnwld')
local first=tonumber(os.getenv('CRUISN_MOTION_FIRST') or '1500')
local last=tonumber(os.getenv('CRUISN_MOTION_LAST') or '8780')
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
