-- Bounded read-only code/state capture for finding each game's HUD producers.
-- Local diagnostic output includes guest code; do not redistribute these dumps.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local game=manager.machine.system.name
local words=({crusnwld24=0x20000,crusnwld=0x20000,offroadc=0x20000,crusnexo=0x40000})[game]
assert(words,'Unsupported drivetrain discovery game')
local target=tonumber(os.getenv('CRUISN_DISCOVERY_FRAME') or '4200')
assert(target and target%1==0 and target>=1 and target<=15000)
return function(n)
 if n~=target then return end
 for _,region in ipairs({{'work',0},{'fast',0x400000}}) do
  local out=assert(io.open('drivetrain-'..region[1]..'.bin','wb'))
  for a=0,words-1 do out:write(string.pack('<I4',s:read_u32(region[2]+a))) end
  out:close()
 end
end
