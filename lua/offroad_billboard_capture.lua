-- SPDX-License-Identifier: BSD-3-Clause
-- Read-only original bit4 billboard transform/projection; no future draw.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local ram=manager.machine.memory.shares[':ram_base'];local frame=0
local first=tonumber(os.getenv('CRUISN_OFFROAD_BILLBOARD_FIRST') or '2500')
local last=tonumber(os.getenv('CRUISN_OFFROAD_BILLBOARD_LAST') or '2520')
assert(first and last and first%1==0 and last%1==0 and first>=1800 and last>=first and last-first<=120,'billboard interval')
local taps,out,current,serial,finished,excluded,failed,busy={},nil,nil,0,0,0,nil,false
local function read(a) if a<0x20000 then return ram:read_u32(a*4) end
 assert((a>=0x809800 and a<0x80a000) or (a>=0xc00000 and a<0x1000000),string.format('billboard read span address=%x pc=%x',a,cpu.state.PC.value));return s:read_u32(a) end
local function words(a,n)local w={};for i=0,n-1 do w[#w+1]=read(a+i) end;return w end
local function guard(fn)return function(...)if busy or failed then return end
 busy=true;local ok,e=pcall(fn,...);busy=false;if not ok then failed=tostring(e) end end end
local function emit(r)
 local keys={};for k in pairs(r)do keys[#keys+1]=k end;table.sort(keys);local v={}
 for _,k in ipairs(keys)do local x=r[k];v[#v+1]='"'..k..'":'..(type(x)=='table' and '['..table.concat(x,',')..']' or tostring(x)) end
 assert(out:write('{'..table.concat(v,',')..'}\n'))
end
local function close()
 for _,t in ipairs(taps)do t:remove()end;taps={}
 if out then assert(out:close());out=nil end
end
local stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failed,failed)
 if n==first then
  assert(manager.machine.system.name=='offroadc')
  for a,w in pairs({[0x1d62]=0x082d120e,[0x1d71]=0x082f120c,[0x1d7f]=0x07271230,
   [0x1d80]=0x087b0003,[0x1db6]=0x152bb70f,[0x1da2]=0x24e22125,[0x1dad]=0x05110002})do assert(read(a)==w,'billboard signature')end
  out=assert(io.open('offroad-billboards.jsonl','w'));out:setvbuf('full',65536)
  taps[#taps+1]=s:install_read_tap(0x1120b,0x1120b,'billboard_owner',guard(function()
   if cpu.state.PC.value==0x1bfd then current=nil end end))
  taps[#taps+1]=s:install_read_tap(0x1120e,0x1120e,'billboard_begin',guard(function(o,d)
   if cpu.state.PC.value~=0x1d63 then return end
   assert(not current,'unfinished billboard');local id=cpu.state.AR6.value;local obj=words(id,22)
   local lod=read(0x1b71a);local descriptor=words(lod,5)
   assert(d==read(0x1120e),'billboard basis read identity')
   if obj[6]&6~=4 or descriptor[1]~=3 or descriptor[4]~=0 then excluded=excluded+1;return end
   serial=serial+1;assert(serial<=4096,'billboard budget')
   local hitindex=obj[8]>>16;local bitsbase=read(0x1b4da);local statebase=read(0x1b4db)
   assert(bitsbase+(hitindex>>5)<0x20000 and statebase+hitindex<0x20000,'hit state span')
   current={id=serial,frame=frame,native_frame=manager.machine.screens[':screen']:frame_number(),
    object=id,object_words=obj,lod=lod,lod_words=descriptor,vertices=words(descriptor[2],12),
    polygons=words(descriptor[5],6),basis_pointer=d,basis=words(d,12),view=words(read(0x1120b),12),
    hitindex=hitindex,hitbits=read(bitsbase+(hitindex>>5)),hitvalue=read(statebase+hitindex)}
  end))
  taps[#taps+1]=s:install_read_tap(0x1120c,0x1120c,'billboard_matrix',guard(function(o,d)
   if cpu.state.PC.value~=0x1d72 or not current then return end
   assert(not current.matrix);current.matrix=words(d,12)
  end))
  taps[#taps+1]=s:install_read_tap(0x11230,0x11230,'billboard_origin',guard(function(o,d)
   if cpu.state.PC.value~=0x1d80 or not current then return end
   assert(current.matrix and not current.origin);current.origin=d
  end))
  taps[#taps+1]=s:install_write_tap(0x1b70f,0x1b70f,'billboard_projected',guard(function(o,d)
   if cpu.state.PC.value~=0x1db7 or not current then return end
   assert(current.origin and current.matrix and current.object==cpu.state.AR6.value)
   local buffer=read(0x11201);assert(d==buffer+12,'billboard four-vertex extent')
   current.projected=words(buffer,12)
   current.reciprocals={}
   for i=3,12,3 do local z=current.projected[i];assert(z<=63679,'original billboard depth')
    current.reciprocals[#current.reciprocals+1]=read(0xcb0fc8+z)end
   current.end_frame=frame;emit(current);finished=finished+1;current=nil
  end))
 elseif n==last+1 then
  close();assert(not failed and finished>0 and finished==serial,'incomplete billboard interval')
  local f=assert(io.open('offroad-billboard-result.json','w'))
  assert(f:write(string.format('{"complete":true,"started":%d,"projected":%d,"excluded":%d,"first":%d,"last":%d}\n',serial,finished,excluded,first,last)));assert(f:close())
 end
end
