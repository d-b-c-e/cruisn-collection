-- SPDX-License-Identifier: BSD-3-Clause
-- Bounded read-only Off Road 1.63 loader/scene probe. Raw resources stay local.
local cpu=manager.machine.devices[':maincpu'];local space=cpu.spaces.program
local ram=manager.machine.memory.shares[':ram_base']
assert(manager.machine.system.name=='offroadc','Off Road section probe revision')
local first=tonumber(os.getenv('CRUISN_OFFROAD_SECTION_FIRST') or '1800')
local last=tonumber(os.getenv('CRUISN_OFFROAD_SECTION_LAST') or '5990')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first and last-first<=20000)
local wanted={};local snapshots=0
for item in string.gmatch(os.getenv('CRUISN_OFFROAD_SECTION_SNAPSHOTS') or '4000,4500,5000,5500,5900','[^,]+') do
 local n=tonumber(item);assert(n and n%1==0 and n>=first and n<=last and not wanted[n])
 wanted[n]=true;snapshots=snapshots+1
end
assert(snapshots<=16,'Off Road snapshot budget')
local frame,busy,failure,taps,live=0,false,nil,{},{}
local records,progress,serial,completed,scenes,saved=nil,nil,0,0,0,0
local function read(p)
 assert(p>=0 and (p<0x20000 or p>=0xc00000 and p<0x1000000),'unmapped Off Road section operand')
 return p<0x20000 and ram:read_u32(p*4) or space:read_u32(p)
end
local function words(p,n)local a={};for i=0,n-1 do a[#a+1]=read(p+i) end;return a end
local function guarded(fn)return function(...)
 if busy or failure then return end
 busy=true;local ok,e=pcall(fn,...);busy=false;if not ok then failure=tostring(e) end
end end
local function emit(out,r)
 local keys={};for k in pairs(r) do keys[#keys+1]=k end;table.sort(keys);local items={}
 for _,k in ipairs(keys) do local v=r[k];items[#items+1]='"'..k..'":'..
  (type(v)=='table' and '['..table.concat(v,',')..']' or tostring(v)) end
 assert(out:write('{'..table.concat(items,',')..'}\n'))
end
local function dump(path,start,count)
 local out=assert(io.open(path,'wb'));local batch={}
 for p=start,start+count-1 do
  batch[#batch+1]=string.pack('<I4',read(p))
  if #batch==1024 then assert(out:write(table.concat(batch)));batch={} end
 end
 if #batch>0 then assert(out:write(table.concat(batch))) end
 assert(out:close())
end
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 for _,r in ipairs(live) do if r.tap then r.tap:remove();r.tap=nil end end
 if records then records:close();records=nil end
 if progress then progress:close();progress=nil end
end
cruisn_offroad_section_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 local remaining={}
 for _,r in ipairs(live) do
  if r.done then r.tap:remove();r.tap=nil else remaining[#remaining+1]=r end
 end
 live=remaining
 if n==first then
  assert(read(0x9c68)==0x6200184d and read(0x9c69)==0x0820b4cd and
   read(0x9c5e)==0x08400205 and read(0x9c19)==0x08400205 and read(0x1bf8)==0x082a11f4)
  records=assert(io.open('offroad-allocations.jsonl','w'));records:setvbuf('full',65536)
  progress=assert(io.open('offroad-section-progress.csv','w'));progress:setvbuf('full',65536)
  progress:write('frame,time,scene,pc,track,current_entry,current,front_entry,front,lead,back_entry,back,trail,mode,count,palette_table,base_palette,base_texture,live_allocations\n')
  dump('offroad-section-rom.bin',0xc00000,0x400000)
  taps[#taps+1]=space:install_read_tap(0x111f4,0x111f4,'offroad_section_scene',guarded(function(o,d,m)
   if cpu.state.PC.value~=0x1bf9 then return end
   scenes=scenes+1;assert(scenes<=40000,'Off Road scene budget')
   local context=words(0x1b4b4,10);local pending=serial-completed
   progress:write(string.format('%d,%.12f,%d,%d,',frame,emu.time(),scenes,cpu.state.PC.value)..
    table.concat(context,',')..string.format(',%d,%d,%d,%d,%d\n',read(0x1b4cc),read(0x1b4cd),read(0x1b4cf),read(0x1b4ce),pending))
   if wanted[frame] then
    wanted[frame]=nil;saved=saved+1
    local stem=string.format('offroad-scene-%d',frame)
    dump(stem..'.bin',0,0x20000)
    local out=assert(io.open(stem..'.json','w'))
    emit(out,{frame=frame,native_frame=manager.machine.screens[':screen']:frame_number(),
     page=space:read_u32(0x980040),time=emu.time(),pc=cpu.state.PC.value,scene=scenes,live_allocations=pending,
     active_slot=d,active_head=read(d),pending_slot=read(0x111f5),pending_head=read(read(0x111f5))});out:close()
   end
  end))
  taps[#taps+1]=space:install_read_tap(0x1b4cd,0x1b4cd,'offroad_section_allocation',guarded(function(o,d,m)
   if cpu.state.PC.value~=0x9c6a then return end
   serial=serial+1;assert(serial<=20000 and serial-completed<=32,'Off Road allocation budget')
   local source=cpu.state.AR2.value-2;local target=cpu.state.AR1.value
   assert(source>=0xc00000 and source+11<=0x1000000 and target>=0 and target+22<=0x20000)
   local r={id=serial,frame=frame,source=source,target=target,source_words=words(source,11),
    palette_table=d,base_palette=read(0x1b4cf),base_texture=read(0x1b4ce),
    flags_clear=read(0x111c2),material_mask=read(0x111c3),material_index_mask=read(0x111c4),
    links_mask=read(0x1123e),post_flags=read(0x11245),post_custom=read(0x11240),section_context=words(0x1b4b4,14)}
   local state={record=r};live[#live+1]=state
   state.tap=space:install_read_tap(target+5,target+5,'offroad_section_final_'..serial,guarded(function(a,value,mask)
    if state.done then return end
    local pc=cpu.state.PC.value;if pc~=0x9c5f and pc~=0x9c1a then return end
    assert(cpu.state.AR2.value==target,'Off Road final descriptor owner')
    r.final_frame=frame;r.final_pc=pc;r.object_words=words(target,22);r.flags=value
    emit(records,r);completed=completed+1;state.done=true
   end))
  end))
 elseif n==last+1 then
  close();assert(serial>0 and serial==completed and scenes>0 and saved==snapshots,'incomplete Off Road section capture')
  local out=assert(io.open('offroad-section-capture.json','w'))
  emit(out,{schema=1,complete=true,first=first,last=last,started=serial,completed=completed,scenes=scenes,snapshots=saved});out:close()
 end
end
