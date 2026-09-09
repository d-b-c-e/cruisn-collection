-- Read-only World 2.4/2.5 future-section residency/progress snapshots. Diagnostic only.
-- Raw snapshots include game resources and MUST stay out of public proof archives.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local revision=manager.machine.system.name=='crusnwld24' and 24 or
 (manager.machine.system.name=='crusnwld' and 25 or nil)
assert(revision,'World 2.4/2.5 future capture only')
local profile=revision==24 and {section=0xd575,stage=0xd5a5,cursor=0xd5a1,remaining=0xd5a2,
 number=0xd57b,flags=0xd57d,palette=0x4151,texture=0x4150} or
 {section=0xd56f,stage=0xd59f,cursor=0xd59b,remaining=0xd59c,
 number=0xd575,flags=0xd577,palette=0x4121,texture=0x4120}
local requested={};local text=os.getenv('CRUISN_FUTURE_FRAMES') or '3000,4500,6000,8500'
for part in text:gmatch('[^,]+') do
 local n=tonumber(part);assert(n and n%1==0 and n>=1800 and n<=12000,'invalid future capture frame')
 assert(not requested[n],'duplicate future capture frame');requested[n]=true
end
local count=0;for _ in pairs(requested) do count=count+1 end
assert(count>0 and count<=16,'bounded future snapshot count required')
local out,rom_done=nil,false
local function dump(name,first,count)
 local f=assert(io.open(name,'wb'));local parts={}
 for i=0,count-1 do
  parts[#parts+1]=string.pack('<I4',s:read_u32(first+i))
  if #parts==1024 then f:write(table.concat(parts));parts={} end
 end
 if #parts>0 then f:write(table.concat(parts)) end;f:close()
end
local function close() if out then out:close();out=nil end end
cruisn_future_stop=emu.add_machine_stop_notifier(close)
return function(n)
 if n==1800 then
  local code={[0x7c6d]=0x0840c700,[0x7c81]=0x084d0705,[0x7c83]=0x08442501,
   [0x7ca9]=0x08400706,[0x7cb0]=0x08442501,[0x7cc8]=0x08400707,
   [0x7ccf]=0x08442501,[0x7cde]=0x08412008,[0x7ce1]=0x0cc02004}
  if revision==25 then
   code={[0x7c5f]=0x0840c700,[0x7c73]=0x084d0705,[0x7c75]=0x08442501,
    [0x7c9b]=0x08400706,[0x7ca2]=0x08442501,[0x7cba]=0x08400707,
    [0x7cc1]=0x08442501,[0x7cd0]=0x08412008,[0x7cd3]=0x0cc02004}
  end
  for p,v in pairs(code) do assert(s:read_u32(p)==v,string.format('future section signature %x',p)) end
  out=assert(io.open('world-future-progress.csv','w'))
  out:write('frame,section,phase,next_definition,remaining,section_number,flags,palette_table,texture_table\n')
 end
 if out and n%2==0 then
  out:write(string.format('%d,%u,%u,%u,%u,%u,%u,%u,%u\n',n,s:read_u32(profile.section),s:read_u32(profile.stage),
   s:read_u32(profile.cursor),s:read_u32(profile.remaining),s:read_u32(profile.number),s:read_u32(profile.flags),
   s:read_u32(profile.palette),s:read_u32(profile.texture)))
 end
 if requested[n] then
  assert(out,'future snapshot before signature guard')
  if not rom_done then dump('world-future-rom.bin',0xc00000,0x400000);rom_done=true end
  dump(string.format('world-future-ram-%d.bin',n),0,0x20000)
  dump(string.format('world-future-fast-%d.bin',n),0x809800,0x800)
 end
end
