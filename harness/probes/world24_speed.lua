-- LOCAL World 2.4 speed producer/HUD observation. No guest writes.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local screen=manager.machine.screens[':screen'];local frame=0
local first,last=1000,9269;local writes,reads,samples=0,0,0
local taps={};local out,hud,snap;local failed=nil;local complete=false
assert(manager.machine.system.name=='crusnwld24')
local function read(a)return s:read_u32(a) end
local function wrap(fn)return function(o,d,m)
 if failed then return end
 local ok,err=pcall(fn,o,d,m);if not ok then failed=tostring(err) end
end end
local function close()
 for _,tap in ipairs(taps) do tap:remove() end;taps={}
 if not out then return end
 out:close();hud:close();snap:close();out=nil
 local f=assert(io.open('world-speed-receipt.json','w'))
 f:write(string.format('{"schema":1,"game":"crusnwld24","first":%d,"last":%d,"complete":%s,"error":%s,"writes":%d,"reads":%d,"samples":%d}\n',first,last,tostring(complete and not failed),failed and string.format('%q',failed) or 'null',writes,reads,samples));f:close()
end
cruisn_world_speed_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failed,failed)
 if n==first then
  assert(read(0x18fc)==0x07400442 and read(0x18fe)==0x0a60e7ae and read(0x18ff)==0x05000000 and read(0x1900)==0x1520ebbd,'speed producer instructions')
  assert(read(0x99f0)==0x0820ebe2 and read(0x99f1)==0x04e00005 and read(0x99f3)==0x04e00004,'HUD lifetime')
  assert(read(0x9a58)==0x05a2ebbd and read(0x9a59)==0x0a620555 and read(0x9a5c)==0x0822ebbd and read(0x9a5e)==0x62008271,'HUD speed consumer')
  out=assert(io.open('world-speed-writes.csv','w'));out:setvbuf('full',65536)
  hud=assert(io.open('world-speed-hud.csv','w'));hud:setvbuf('full',65536)
  snap=assert(io.open('world-speed-frames.csv','w'));snap:setvbuf('full',65536)
  out:write('sequence,seconds,native_frame,frame,pc,mask,state,flags,player,actor,raw,display\n')
  hud:write('sequence,seconds,native_frame,frame,pc,state,player,display\n')
  snap:write('frame,seconds,state,flags,player,raw,display\n')
  taps[#taps+1]=s:install_write_tap(0xebbd,0xebbd,'world_speed_producer',wrap(function(o,d,m)
   writes=writes+1;assert(writes<=20000,'speed write budget')
   local pc=cpu.state.PC.value;local p=read(0xee0e);local actor=cpu.state.AR4.value;local raw=0x80000000
   if pc==0x1901 then assert(actor==p and p>=0x1000 and p+0x42<0x20000 and m==0xffffffff,'speed owner/mask');raw=read(p+0x42) end
   out:write(string.format('%d,%.12f,%d,%d,%x,%x,%d,%x,%x,%x,%x,%u\n',writes,emu.time(),screen:frame_number(),frame,pc,m,read(0xebe2),read(0xebe3),p,actor,raw,d))
  end))
  taps[#taps+1]=s:install_read_tap(0xebbd,0xebbd,'world_speed_hud',wrap(function(o,d,m)
   local pc=cpu.state.PC.value
   if pc~=0x9a59 and pc~=0x9a5d then return end
   reads=reads+1;assert(reads<=20000 and m==0xffffffff,'HUD read budget/mask')
   hud:write(string.format('%d,%.12f,%d,%d,%x,%d,%x,%u\n',reads,emu.time(),screen:frame_number(),frame,pc,read(0xebe2),read(0xee0e),d))
  end))
 end
 if out and n<=last then
  local p=read(0xee0e);local raw=0x80000000
  if p>=0x1000 and p+0x42<0x20000 then raw=read(p+0x42) end
  snap:write(string.format('%d,%.12f,%d,%x,%x,%x,%u\n',n,emu.time(),read(0xebe2),read(0xebe3),p,raw,read(0xebbd)))
  samples=samples+1
 end
 if n==last then complete=true;close() end
end
