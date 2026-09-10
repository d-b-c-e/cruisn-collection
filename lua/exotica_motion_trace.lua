-- Exotica2.4 camera words and actual ADC reads/times; no input synthesis.
-- Main RAM share avoids read handlers; only the bounded internal matrix is read.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local ram=manager.machine.memory.shares[':ram_base']
assert(manager.machine.system.name=='crusnexo')
local first=tonumber(os.getenv('CRUISN_EXOTICA_MOTION_FIRST') or '1800')
local last=tonumber(os.getenv('CRUISN_EXOTICA_MOTION_LAST') or '5990')
assert(first and last and first%1==0 and last%1==0 and first>=1800 and last>=first and last<=16000)
local frame,tap,camera,adc,failed=0,nil,nil,nil,nil
local function read(p)return ram:read_u32(p*4) end
local function close()if tap then tap:remove();tap=nil end;if camera then camera:close();adc:close();camera=nil;adc=nil end end
cruisn_exotica_motion_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failed,failed)
 if n==first then
  assert(read(0x67bf)==0x87ff35 and read(0x67bd)==0xfeb and read(0x67c3)==0x87ff48)
  camera=assert(io.open('exotica-camera.csv','w'));camera:setvbuf('full',65536)
  camera:write('frame,x,y,z,m0,m1,m2,m3,m4,m5,m6,m7,m8\n')
  adc=assert(io.open('exotica-adc.csv','w'));adc:setvbuf('full',65536)
  adc:write('frame,time,pc,address,value\n')
  tap=s:install_read_tap(0x9c0000,0x9c000f,'exotica_actual_adc',function(o,d,m)
   if failed then return end;local ok,e=pcall(function()assert(adc:write(string.format('%d,%.12f,%x,%x,%x\n',frame,emu.time(),cpu.state.PC.value,o,d))) end)
   if not ok then failed=tostring(e) end
  end)
 end
 if camera and n<=last then
  camera:write(n);for p=0xfeb,0xfed do camera:write(string.format(',%08x',read(p))) end
  for p=0x87ff35,0x87ff3d do camera:write(string.format(',%08x',s:read_u32(p))) end
  camera:write('\n')
 end
 if n==last+1 then close() end
end
