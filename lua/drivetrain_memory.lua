-- Independent read-only samples for the non-USA drivetrain consumers.
local s=manager.machine.devices[':maincpu'].spaces.program
local game=manager.machine.system.name
local first=tonumber(os.getenv('CRUISN_TACH_FIRST') or '1000')
local last=tonumber(os.getenv('CRUISN_TACH_LAST') or '6000')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first and last-first<=12000)
assert(game=='crusnwld' or game=='offroadc' or game=='crusnexo')
local out
local function close() if out then out:close();out=nil end end
cruisn_game_drivetrain_stop=emu.add_machine_stop_notifier(close)
return function(n)
 if n==first then
  if game=='crusnwld' then assert(s:read_u32(0x9ad0)==0x07400052 and s:read_u32(0x9ad1)==0x0a60e6aa)
  elseif game=='offroadc' then assert(s:read_u32(0xaca7)==0x07420436 and s:read_u32(0xad9b)==0x0852040b)
  else assert(s:read_u32(0xc2c1)==0x07400063 and s:read_u32(0xc2c2)==0x0a60f2ac) end
  out=assert(io.open('drivetrain-memory.csv','w'))
  out:write('frame,player,gear,rev_raw,state,flags,hud_speed_raw,hud_tach_raw\n')
 end
 if out and n<=last then
  local p,gear,rev,state,flags,spd,tach,go,ro,max=0,0,0x80000000,0,0,0,0,0,0,0x20000
  if game=='crusnwld' then
   p=s:read_u32(0xee08);go=0x51;ro=0x52;state=s:read_u32(0xebdc);flags=s:read_u32(0xebdd)
  elseif game=='offroadc' then
   p=s:read_u32(0x19d25)+0xbc*s:read_u32(0x1c86c);go=0xb;ro=0x36
   state=s:read_u32(0x1c0dc);flags=s:read_u32(0x1995e);spd=s:read_u32(0x19d11);tach=s:read_u32(0x1987c)
  else
   p=s:read_u32(0x10be);go=0x62;ro=0x63;max=0x40000
   state=s:read_u32(0x76);flags=s:read_u32(0x79);spd=s:read_u32(0x1074);tach=s:read_u32(0x1049)
  end
  if p>=0x1000 and p+ro<max then gear=s:read_u32(p+go);rev=s:read_u32(p+ro) end
  out:write(string.format('%d,%x,%d,%x,%d,%x,%x,%x\n',n,p,gear,rev,state,flags,spd,tach))
 end
 if n==last then close() end
end
