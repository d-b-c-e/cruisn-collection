-- Independent World 2.4 tach/gear consumer and lifetime evidence; read-only.
local s=manager.machine.devices[':maincpu'].spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 only')
local first=tonumber(os.getenv('CRUISN_TACH_FIRST') or '1000')
local last=tonumber(os.getenv('CRUISN_TACH_LAST') or '9269')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first and last-first<=12000)
local out
local function close() if out then out:close();out=nil end end
cruisn_world_drivetrain_stop=emu.add_machine_stop_notifier(close)
return function(n)
 if n==first then
  assert(s:read_u32(0x9ada)==0x0828ee0e and s:read_u32(0x9adb)==0x07400052 and
         s:read_u32(0x9adc)==0x0a60e6aa and s:read_u32(0x9af3)==0x08400051,'World tach/gear instructions')
  out=assert(io.open('world-drivetrain-memory.csv','w'))
  out:write('frame,state,flags,player,gear,rev_raw,speed_raw,palette_lit\n')
 end
 if out and n<=last then
  local p=s:read_u32(0xee0e)
  local gear,rev,speed=0,0x80000000,0x80000000
  if p>=0x1000 and p+0x52<0x20000 then
   gear=s:read_u32(p+0x51);rev=s:read_u32(p+0x52);speed=s:read_u32(p+0x42)
  end
  local lit=0
  for i=0,21 do if s:read_u32(0xebc2+i)~=0 then lit=lit+1 end end
  out:write(string.format('%d,%d,%x,%x,%d,%x,%x,%d\n',n,s:read_u32(0xebe2),s:read_u32(0xebe3),p,gear,rev,speed,lit))
 end
 if n==last then close() end
end
