-- Read-only USA v4.5 drivetrain/HUD provenance; no input or memory mutation.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnusa','USA v4.5 only')
local first=tonumber(os.getenv('CRUISN_TACH_FIRST') or '2520')
local last=tonumber(os.getenv('CRUISN_TACH_LAST') or '5012')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first and last-first<=9000)
local out
local function close() if out then out:close();out=nil end end
cruisn_drivetrain_stop=emu.add_machine_stop_notifier(close)
return function(n)
 if n==first then
  assert(s:read_u32(0x9e53)==0x0828e8a8 and s:read_u32(0x9e54)==0x07400039 and
         s:read_u32(0x9e55)==0x0a60e6aa and s:read_u32(0x9e6b)==0x08400038,'USA tach/gear instructions')
  out=assert(io.open('drivetrain-memory.csv','w'))
  out:write('frame,player,gear,rev_raw,palette_lit')
  for i=0,21 do out:write(',palette'..i) end
  out:write('\n')
 end
 if out and n<=last then
  local p=s:read_u32(0xe8a8)
  assert(p>=0x1000 and p+0x40<0x20000,'player pointer out of work RAM')
  local colors,lit={},0
  for i=0,21 do colors[i]=s:read_u32(0x9e55ea+i);if colors[i]~=0 then lit=lit+1 end end
  out:write(string.format('%d,%x,%d,%x,%d',n,p,s:read_u32(p+0x38),s:read_u32(p+0x39),lit))
  for i=0,21 do out:write(string.format(',%x',colors[i])) end
  out:write('\n')
 end
 if n==last then close() end
end
