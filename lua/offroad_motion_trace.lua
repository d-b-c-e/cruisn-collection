-- Read-only Off Road1.63 camera/actual ADC trace. No distance or resource taps.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='offroadc','Off Road1.63 only')
local first=tonumber(os.getenv('CRUISN_MOTION_FIRST') or '1800')
local last=tonumber(os.getenv('CRUISN_MOTION_LAST') or '5990')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>first and last-first<=12000)
local frame,tap,camera,adc,failed=0,nil,nil,nil,nil
local function close()
 if tap then tap:remove();tap=nil end
 if camera then assert(camera:close());assert(adc:close());camera=nil;adc=nil end
end
cruisn_offroad_motion_stop=emu.add_machine_stop_notifier(close)
return function(n)
 assert(not failed,failed);frame=n
 if n==first then
  assert(s:read_u32(0x1bfc)==0x082f120b and s:read_u32(0x1120b)==0x196f3,'camera signature mismatch')
  camera=assert(io.open('offroad-camera.csv','w'));camera:setvbuf('full',65536)
  assert(camera:write('frame,x,y,z,m0,m1,m2,m3,m4,m5,m6,m7,m8\n'))
  adc=assert(io.open('offroad-adc.csv','w'));adc:setvbuf('full',65536)
  assert(adc:write('frame,time,pc,value\n'))
  tap=s:install_read_tap(0x993000,0x993000,'offroad_actual_adc',function(o,d)
   if failed then return end
   local ok,reason=pcall(function()
    assert(adc:write(string.format('%d,%.12f,%x,%x\n',frame,emu.time(),cpu.state.PC.value,d)))
   end)
   if not ok then failed=tostring(reason) end
  end)
 end
 if camera and n<=last then
  assert(s:read_u32(0x1120b)==0x196f3,'camera pointer changed')
  assert(camera:write(n))
  for _,i in ipairs({3,7,11,0,1,2,4,5,6,8,9,10}) do assert(camera:write(string.format(',%08x',s:read_u32(0x196f3+i)))) end
  assert(camera:write('\n'))
 end
 if n==last+1 then close() end
end
