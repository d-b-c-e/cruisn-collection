-- SPDX-License-Identifier: BSD-3-Clause
-- Bounded, read-only scene operands and matching materials for offline trials.
-- No allocation tracing, texture-write observer, guest mutation or physical FFB.
local cpu=manager.machine.devices[':maincpu'];local space=cpu.spaces.program
local ram=assert(manager.machine.memory.shares[':ram_base'])
local texture=assert(manager.machine.memory.shares[':textureram'])
local palette=assert(manager.machine.memory.shares[':paletteram'])
local revision=manager.machine.system.name=='crusnwld24' and 24 or
 (manager.machine.system.name=='crusnwld' and 25 or nil)
assert(revision,'World 2.4/2.5 resource capture only')
local scene_head=revision==24 and 0x61ee or 0x658f
local first=tonumber(os.getenv('CRUISN_WORLD_RESOURCE_FIRST') or '1800')
local last=tonumber(os.getenv('CRUISN_WORLD_RESOURCE_LAST') or '7341')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first and last-first<=20000)
local wanted={};local budget=0
for item in string.gmatch(os.getenv('CRUISN_WORLD_RESOURCE_FRAMES') or '7337,7339','[^,]+') do
 local n=tonumber(item);assert(n and n%1==0 and n>=first and n<=last-2 and not wanted[n],
  'native resource frames require two replay ticks before probe end')
 wanted[n]=true;budget=budget+1
end
assert(budget>=1 and budget<=8,'World resource snapshot budget')
local frame,saved,busy,failure,tap=0,0,false,nil,nil
local function read(p)assert(p>=0 and p<0x20000);return ram:read_u32(4*p) end
local function emit(path,values)
 local keys={};for k in pairs(values) do keys[#keys+1]=k end;table.sort(keys)
 local fields={};for _,k in ipairs(keys) do fields[#fields+1]='"'..k..'":'..tostring(values[k]) end
 local out=assert(io.open(path,'w'));assert(out:write('{'..table.concat(fields,',')..'}\n'));assert(out:close())
end
local function dump(path,count,reader)
 local out=assert(io.open(path,'wb'));local batch={}
 for p=0,count-1 do
  batch[#batch+1]=string.pack('<I4',reader(p))
  if #batch==1024 then assert(out:write(table.concat(batch)));batch={} end
 end
 if #batch>0 then assert(out:write(table.concat(batch))) end
 assert(out:close())
end
local function close()if tap then tap:remove();tap=nil end end
cruisn_world_resource_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 if n==first then
  assert(read(0x69)==(0x08280000|scene_head) and read(0x7d)==0x082a0041 and read(0x7f)==0x082d0043)
  emit('world-resource-capture.json',{schema=1,complete=false,first=first,last=last,requested=budget,saved=0})
  dump('world-resource-rom.bin',0x400000,function(p)return space:read_u32(0xc00000+p)end)
  tap=space:install_read_tap(scene_head,scene_head,'world_scene_resources',function()
   if busy or failure or cpu.state.PC.value~=0x6a then return end
   -- Replay callbacks and native scene execution need not share a frame label.
   -- Match native display frames and preserve the replay label as separate data.
   local scene_frame=manager.machine.screens[':screen']:frame_number()
   if not wanted[scene_frame] then return end
   busy=true
   local ok,e=pcall(function()
    local stem=string.format('world-resource-%d',scene_frame)
    dump(stem..'-ram.bin',0x20000,function(p)return ram:read_u32(4*p)end)
    dump(stem..'-fast.bin',0x800,function(p)return space:read_u32(0x809800+p)end)
    dump(stem..'-textures.bin',0x200000,function(p)return texture:read_u32(4*p)end)
    dump(stem..'-palettes.bin',0x8000,function(p)return palette:read_u32(4*p)end)
    emit(stem..'.json',{schema=1,frame=scene_frame,native_frame=scene_frame,replay_frame=frame,
     time=emu.time(),page=space:read_u32(0x980040),pc=cpu.state.PC.value,revision=revision,section=read(revision==24 and 0xd575 or 0xd56f),fast_words=0x800,
     texture_words=0x200000,palette_words=0x8000,ram_words=0x20000})
    wanted[scene_frame]=nil;saved=saved+1
   end)
   busy=false;if not ok then failure=tostring(e) end
  end)
 elseif n==last+1 then
  close();assert(saved==budget,'incomplete World scene resources')
  emit('world-resource-capture.json',{schema=1,complete=true,first=first,last=last,requested=budget,saved=saved})
 end
end
