-- Read-only USA section frontiers. Raw ROM/RAM snapshots MUST remain local.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local ram=assert(manager.machine.memory.shares[':ram_base'])
assert(manager.machine.system.name=='crusnusa')
local first,last=1800,5010
local frames={3000,3500,4000,4500,4900};local next_capture=1
local resources=os.getenv('CRUISN_USA_FUTURE_RESOURCES')=='1'
local frame,tap,out,busy,failure,rom_done,scenes=0,nil,nil,false,nil,false,0
local function read(p)
 if p>=0 and p<0x20000 then return ram:read_u32(p*4)end
 assert(p>=0x809800 and p<0x80a000 or p>=0xc00000 and p<0x1000000,'unsafe future read')
 return s:read_u32(p)
end
local function dump(name,start,count,get)
 get=get or read
 local f=assert(io.open(name,'wb'));local parts={}
 for i=0,count-1 do
  parts[#parts+1]=string.pack('<I4',get(start+i))
  if #parts==1024 then f:write(table.concat(parts));parts={}end
 end
 if #parts>0 then f:write(table.concat(parts))end;f:close()
end
local function close()
 if tap then tap:remove();tap=nil end
 if out then
  out:close();out=nil
  local f=assert(io.open('usa-future-capture.json','w'))
  f:write(string.format('{"schema":1,"first":%d,"last":%d,"scenes":%d,"snapshots":%d,"complete":%s}\n',
   first,last,scenes,next_capture-1,(not failure and frame>last and next_capture>#frames)and'true'or'false'))
  f:close()
 end
end
cruisn_usa_future_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 if n==first then
  for p,v in pairs({[0x80]=0x08280040,[0x401a]=0x0828e49d,[0x403b]=0x1528e49d,
   [0x4096]=0x082ae4a5,[0x40a1]=0x152ae4a5,[0x40b9]=0x62007035})do
   assert(read(p)==v,'USA future signature mismatch')
  end
  out=assert(io.open('usa-future-progress.csv','w'));out:setvbuf('full',65536)
  out:write('frame,native_frame,time,page,track,loading,next_section,section_number,stage,flags\n')
  tap=s:install_read_tap(0x40,0x40,'usa_future_scene',function()
   if busy or failure or cpu.state.PC.value~=0x81 then return end;busy=true
   local ok,reason=pcall(function()
    scenes=scenes+1
    local native=manager.machine.screens[':screen']:frame_number()
    local clock=emu.time();local page=s:read_u32(0x980040)
    out:write(string.format('%d,%d,%.12f,%d,%u,%u,%u,%u,%u,%u\n',frame,native,clock,page,
     read(0xa12e),read(0xe49d),read(0xe4a5),read(0xe4a4),read(0xe4ab),read(0xe4aa)))
    if next_capture<=#frames and frame>=frames[next_capture]then
     if not rom_done then dump('usa-future-rom.bin',0xc00000,0x400000);rom_done=true end
     dump(string.format('usa-future-ram-%d.bin',frame),0,0x20000)
     dump(string.format('usa-future-fast-%d.bin',frame),0x809800,0x800)
     if resources then
      local texture=assert(manager.machine.memory.shares[':textureram'])
      local palette=assert(manager.machine.memory.shares[':paletteram'])
      dump(string.format('usa-future-textures-%d.bin',frame),0,0x200000,function(p)return texture:read_u32(4*p)end)
      dump(string.format('usa-future-palettes-%d.bin',frame),0,0x8000,function(p)return palette:read_u32(4*p)end)
     end
     local f=assert(io.open(string.format('usa-future-scene-%d.json',frame),'w'))
     f:write(string.format('{"frame":%d,"native_frame":%d,"time":"%.12f","page":%d}\n',frame,native,clock,page));f:close()
     next_capture=next_capture+1
    end
   end)
   busy=false;if not ok then failure=tostring(reason)end
  end)
 elseif n==last+1 then close();assert(next_capture>#frames and scenes>0,'incomplete USA future snapshots')end
end
