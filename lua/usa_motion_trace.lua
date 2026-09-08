-- Read-only, bounded USA 4.5 camera and actual ADC-read timeline. Camera state is
-- a route-divergence detector, not a claim that these words are vehicle physics.
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnusa','USA4.5 only')
local first=tonumber(os.getenv('CRUISN_MOTION_FIRST') or '1800')
local last=tonumber(os.getenv('CRUISN_MOTION_LAST') or '5000')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=12000,'invalid motion trace interval')
local frame,taps,out,adc,failed=0,{},nil,nil,nil
local function close()
    for _,t in ipairs(taps) do t:remove() end
    taps={}
    if out then out:close();adc:close();out=nil end
end
cruisn_usa_motion_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    assert(not failed,failed)
    if n==first then
        assert(s:read_u32(0x9d)==0x082e0045 and s:read_u32(0xa8)==0x082d0047,'camera path signature')
        out=assert(io.open('usa-camera.csv','w'))
        out:setvbuf('full',65536)
        out:write('frame,x,y,z,m0,m1,m2,m3,m4,m5,m6,m7,m8\n')
        adc=assert(io.open('usa-adc.csv','w'));adc:setvbuf('full',65536);adc:write('frame,time,pc,value\n')
        table.insert(taps,s:install_read_tap(0x993000,0x993000,'usa_actual_adc',function(o,d,m)
            if failed then return end
            local ok,reason=pcall(function()
                assert(adc:write(string.format('%d,%.12f,%x,%x\n',frame,emu.time(),cpu.state.PC.value,d)))
            end)
            if not ok then failed=tostring(reason) end
        end))
    end
    if out and n<=last then
        local p=s:read_u32(0x45);local m=s:read_u32(0x47)
        assert(p==0x809800 and m==0x809809,'camera pointers outside expected RAM')
        out:write(n)
        for i=0,2 do out:write(string.format(',%08x',s:read_u32(p+i))) end
        for i=0,8 do out:write(string.format(',%08x',s:read_u32(m+i))) end
        out:write('\n')
    end
    if n==last+1 then close() end
end
