-- SPDX-License-Identifier: BSD-3-Clause
-- Bounded, read-only Exotica2.4 allocation/frontier probe. Raw resources stay LOCAL.
-- Loader activity covers entry B7E8 through the final position store B840.
local first=tonumber(os.getenv('CRUISN_EXOTICA_SECTION_FIRST') or '1800')
local last=tonumber(os.getenv('CRUISN_EXOTICA_SECTION_LAST') or '5990')
assert(first and last and first%1==0 and last%1==0 and first>=1800 and last>=first and last-first<=20000)
local wanted,snapshot_count,saved={},0,0
for item in string.gmatch(os.getenv('CRUISN_EXOTICA_SECTION_SNAPSHOTS') or '3500,4000,4500,5000,5500,5990','[^,]+') do
 local n=tonumber(item);assert(n and n%1==0 and n>=first and n<=last and not wanted[n])
 wanted[n]=true;snapshot_count=snapshot_count+1
end
assert(snapshot_count>0 and snapshot_count<=16,'Exotica snapshot budget')
local cpu=manager.machine.devices[':maincpu'];local space=cpu.spaces.program
local ram=manager.machine.memory.shares[':ram_base'];local screen=manager.machine.screens[':screen']
assert(manager.machine.system.name=='crusnexo')
local frame,busy,failure,serial=0,false,nil,0
local tap,out,final,waiting=nil,nil,nil,nil
local begin_tap,end_tap,progress=nil,nil,nil
local loading,section_starts,section_ends=0,0,0
local function read(p)
 assert(p>=0 and p%1==0 and (p<0x40000 or p>=0x87fe00 and p<0x880000 or p>=0xa00000 and p<0x1000000),'Exotica section operand')
 return p<0x40000 and ram:read_u32(p*4) or space:read_u32(p)
end
local function words(p,n)local result={};assert(n>=0 and n<=128);for i=0,n-1 do result[#result+1]=read(p+i) end;return result end
local function binding(token,table_pointer)
 local base=read(table_pointer+((token>>28)&15));assert(base~=0,'empty material bank')
 local slot=base+(token&0x3fff);return {token,base,slot,read(slot)}
end
local function dump_ram(path)
 local file=assert(io.open(path,'wb'));local batch={}
 for p=0,0x3ffff do
  batch[#batch+1]=string.pack('<I4',read(p))
  if #batch==1024 then assert(file:write(table.concat(batch)));batch={} end
 end
 assert(file:close())
end
local function dump_rom(name,expected,path)
 local region=assert(manager.machine.memory.regions[name]);assert(region.size==expected)
 local file=assert(io.open(path,'wb'));local data=region:read(0,region.size)
 assert(#data==expected and file:write(data));assert(file:close())
end
local function emit(r)
 local keys={};for k in pairs(r) do keys[#keys+1]=k end;table.sort(keys);local parts={}
 for _,k in ipairs(keys) do local v=r[k];parts[#parts+1]='"'..k..'":'..(type(v)=='table' and '['..table.concat(v,',')..']' or tostring(v)) end
 assert(out:write('{'..table.concat(parts,',')..'}\n'))
end
local function guarded(fn)return function(...)
 if busy or failure then return end;busy=true;local ok,e=pcall(fn,...);busy=false;if not ok then failure=tostring(e) end
end end
local function close()
 if begin_tap then begin_tap:remove();begin_tap=nil end
 if end_tap then end_tap:remove();end_tap=nil end
 if progress then progress:close();progress=nil end
 if tap then tap:remove();tap=nil end;if final then final:remove();final=nil end
 if out then out:close();out=nil end
end
cruisn_exotica_section_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 if n==first then
  assert(read(0xb859)==0x082267c4 and read(0xb8cb)==0x0840041d and read(0xb7e8)==0x082e0597 and read(0xb840)==0x1420059b)
  out=assert(io.open('exotica-section-allocations.jsonl','w'));out:setvbuf('full',65536)
  progress=assert(io.open('exotica-section-progress.csv','w'));progress:setvbuf('full',65536)
  progress:write('frame,time,native_frame,pc,bank,loading,starts,ends,allocating,track,entry,cursor,section,current,lead,mode\n')
  dump_rom(':maindata',0x800000,'exotica-main-rom.bin')
  dump_rom(':bankeddata',0x3000000,'exotica-banked-rom.bin')
  begin_tap=space:install_read_tap(0x597,0x597,'exotica_section_begin',guarded(function(o,d,m)
   if cpu.state.PC.value~=0xb7e9 then return end
   assert(loading==0);loading=d;section_starts=section_starts+1
  end))
  end_tap=space:install_write_tap(0x59b,0x59b,'exotica_section_end',guarded(function(o,d,m)
   if cpu.state.PC.value~=0xb841 then return end
   assert(loading~=0 and read(0x597)==loading+4);loading=0;section_ends=section_ends+1
  end))
  tap=space:install_read_tap(0x67c4,0x67c4,'exotica_section_position',guarded(function(o,d,m)
   if cpu.state.PC.value~=0xb85a then return end
   assert(waiting==nil,'unfinished Exotica allocation');serial=serial+1;assert(serial<=10000)
   local object=cpu.state.AR4.value;assert(object>=0x1000 and object+32<=0x40000)
   local source=cpu.state.AR5.value-4
   local definition=words(source,6);local model=words(definition[1]&0xffffff,6)
   local material=model[3]
   local texture=binding(material&0xf0003fff,read(0xe67c))
   local palette=binding((material&0xf0000000)|((material&0x0fffc000)>>14),read(0xe67d))
   local override={};if ((definition[6]>>16)&0x3ff)~=0 then override=binding(((definition[6]>>16)&0x3ff)|(read(0xf5)<<28),read(0xe67d)) end
   waiting={id=serial,frame=frame,native_frame=screen:frame_number(),time=emu.time(),object=object,source=source,
    definition=definition,model_words=model,texture_binding=texture,palette_binding=palette,override_binding=override,
    constants=words(0xbbaa,11),bank=space:read_u32(0x8d0005),track=read(read(0xe9)+read(0x1fbc)),section=read(0x597),section_words=words(read(0x597),4),
    first_list=cpu.state.AR3.value,list_header=words(cpu.state.AR3.value-4,5),
    flags=cpu.state.R6.value,gap=cpu.state.R7.value,remaining=cpu.state.R4.value,
    scalars=words(0x58e,16),matrix=words(d,9),initial=words(object,32),trig=words(0xe991,7),
    material_tables={read(0xe67c),read(0xe67d)},material_banks=words(read(0xe67c),16),palette_banks=words(read(0xe67d),16)}
   final=space:install_read_tap(object+0x1d,object+0x1d,'exotica_section_ready',guarded(function(a,v,mask)
    if cpu.state.PC.value~=0xb8cc then return end
    assert(waiting and waiting.object==cpu.state.AR4.value)
    waiting.actual=words(waiting.object,32);waiting.final_time=emu.time();waiting.final_native_frame=screen:frame_number()
    emit(waiting);waiting=nil
    local old=final;final=nil;old:remove()
   end))
  end))
 end
 if n>=first and n<=last then
  local bank=space:read_u32(0x8d0005)
  progress:write(string.format('%d,%.12f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n',
   n,emu.time(),screen:frame_number(),cpu.state.PC.value,bank,loading,section_starts,section_ends,waiting and 1 or 0,
   read(read(0xe9)+read(0x1fbc)),read(0x597),read(0x598),read(0x590),read(0x10c0),read(0x591),read(0x596)))
  if wanted[n] then
   wanted[n]=nil;saved=saved+1
   dump_ram(string.format('exotica-section-%d.bin',n))
  end
 end
 if n==last+1 then
  assert(section_starts==section_ends and loading==0 and serial>0 and waiting==nil and saved==snapshot_count,'incomplete Exotica section capture')
  close()
  local receipt=assert(io.open('exotica-section-capture.json','w'))
  assert(receipt:write(string.format('{"schema":1,"complete":true,"first":%d,"last":%d,"allocations":%d,"sections":%d,"snapshots":%d}\n',first,last,serial,section_starts,saved)))
  assert(receipt:close())
 end
end
