-- Read-only adapter mapping snapshots. Contains game data: keep raw files local.
local game=manager.machine.system.name
local supported={crusnusa=true,crusnwld24=true,crusnwld=true,offroadc=true,crusnexo=true}
assert(supported[game],'unsupported scenery adapter snapshot game')
local frame=tonumber(os.getenv('CRUISN_ADAPTER_FRAME') or '3000')
assert(frame and frame%1==0 and frame>=1800 and frame<=12000,'invalid adapter snapshot frame')
local s=manager.machine.devices[':maincpu'].spaces.program
local function dump(name,first,count)
 local out=assert(io.open(name,'wb'));local parts={}
 for i=0,count-1 do
  parts[#parts+1]=string.pack('<I4',s:read_u32(first+i))
  if #parts==1024 then out:write(table.concat(parts));parts={} end
 end
 if #parts>0 then out:write(table.concat(parts)) end;out:close()
end
return function(n)
 if n~=frame then return end
 -- Platform mappings verified in midvunit_map/zeus2_map. Do not read I/O,
 -- telemetry ports, bank selectors or nonvolatile configuration registers.
 local zeus=game=='crusnexo'
 dump('adapter-ram.bin',0,zeus and 0x40000 or 0x20000)
 dump('adapter-fast.bin',0x400000,zeus and 0x40000 or 0x20000)
 dump('adapter-rom.bin',zeus and 0xa00000 or 0xc00000,zeus and 0x200000 or 0x400000)
 if zeus then dump('adapter-current-bank.bin',0xc00000,0x400000) end
 local out=assert(io.open('adapter-snapshot.json','w'))
 out:write(string.format('{"game":"%s","frame":%d,"rom_base":%d,"current_bank_only":%s}\n',
  game,n,zeus and 0xa00000 or 0xc00000,zeus and 'true' or 'false'));out:close()
end
