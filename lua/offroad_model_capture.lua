-- Bounded Off Road 1.63 ordinary-model capture; no guest writes or allocations.
-- Use with replay.py --probe-script and CRUISN_OFFROAD_MODEL_FIRST/LAST.
-- Raw ROM/model/material operands must remain local and outside public archives.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local ram=manager.machine.memory.shares[':ram_base']
assert(manager.machine.system.name=='offroadc')
local first=tonumber(os.getenv('CRUISN_OFFROAD_MODEL_FIRST') or '2500')
local last=tonumber(os.getenv('CRUISN_OFFROAD_MODEL_LAST') or '2550')
assert(first and last and first%1==0 and last%1==0 and first>=1800 and last>=first and last-first<=120,'Off Road model interval')
local frame,taps,out,draws,current,serial,failure,busy=0,{},nil,nil,nil,0,nil,false
local projected_count,draw_count,excluded_count,complete=0,0,0,false
local dma,page={},0
local function read(p)
 assert(p>=0 and (p<0x20000 or p>=0x809800 and p<0x80a000 or p>=0xc00000 and p<0x1000000),'unmapped Off Road operand')
 if p<0x20000 then return ram:read_u32(p*4) end
 return s:read_u32(p)
end
local function words(p,n)
 assert(n>=0 and n<=8192,'Off Road operand count')
 local a={};for i=0,n-1 do a[#a+1]=read(p+i) end;return a
end
local function guard(fn) return function(...)
 if busy or failure then return end;busy=true
 local ok,e=pcall(fn,...);busy=false;if not ok then failure=tostring(e) end
end end
local function emit(r)
 local keys={};for k in pairs(r) do keys[#keys+1]=k end;table.sort(keys);local parts={}
 for _,k in ipairs(keys) do local v=r[k];parts[#parts+1]='"'..k..'":'..(type(v)=='table' and '['..table.concat(v,',')..']' or tostring(v)) end
 assert(out:write('{'..table.concat(parts,',')..'}\n'))
end
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if out then
  out:close();draws:close();out=nil
  local f=assert(io.open('offroad-model-capture.json','w'))
  f:write(string.format('{"first":%d,"last":%d,"started":%d,"projected":%d,"draws":%d,"excluded_clipped_or_special":%d,"complete":%s}\n',first,last,serial,projected_count,draw_count,excluded_count,tostring(complete)));f:close()
 end
end
cruisn_offroad_model_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 if n==first then
  for p,v in pairs({[0x1def]=0x082ab71a,[0x1df3]=0x085b2201,[0x1e22]=0x24e22125,[0x1f63]=0x085b1201,[0x1fb7]=0x1541c600,[0x1ff4]=0x1541c600}) do assert(read(p)==v,'Off Road model signature') end
  out=assert(io.open('offroad-model-transform.jsonl','w'));out:setvbuf('full',65536)
  draws=assert(io.open('offroad-model-draws.csv','w'));draws:setvbuf('full',65536)
  draws:write('frame,call,object,model,pc,page,flags,palette,x0,y0,x1,y1,x2,y2,x3,y3,uv0,uv1,uv2,uv3,texture,word15\n')
  local f=assert(io.open('offroad-model-reciprocals.bin','wb'));local base=read(0x111a7)
  assert(base==0xcb0fc8,'Off Road reciprocal table changed')
  for i=-4096,63679 do f:write(string.pack('<I4',read(base+i))) end;f:close()
  local trigbase=read(0x1117b);assert(trigbase==0xc23e97,'Off Road trig table changed')
  local t=assert(io.open('offroad-model-trig.bin','wb'));for i=-1,16384 do t:write(string.pack('<I4',read(trigbase+i))) end;t:close()
  page=s:read_u32(0x980040)
  taps[#taps+1]=s:install_read_tap(0x1120b,0x1120b,'offroad_model_owner',guard(function(o,d,m)
   if cpu.state.PC.value==0x1bfd then current=nil end
  end))
  taps[#taps+1]=s:install_read_tap(0x1b71a,0x1b71a,'offroad_model_start',guard(function(o,d,m)
   if cpu.state.PC.value~=0x1df0 then return end
   assert(cpu.state.DP.value==1,'Off Road data page changed')
   current=nil
   local id=cpu.state.AR6.value;local obj=words(id,22);local vertices=read(d)+1;local polygons=read(d+3)+1
   -- The captured ordinary path owns XY only, despite its three-word stride.
   if read(0x1b704)~=0 or (obj[6]&0x2008)~=0 then excluded_count=excluded_count+1;return end
   assert(vertices>=1 and vertices<=512 and polygons>=1 and polygons<=1024,'Off Road model count')
   serial=serial+1;assert(serial<=20000,'Off Road bounded capture')
   current={schema=1,call=serial,frame=frame,object=id,model=obj[21],lod=d,lod_words=words(d,5),
    object_words=obj,vertices=vertices,polygons=polygons,vertex_buffer=read(0x11201),
    vertex_words=words(read(d+1),3*vertices),polygon_words=words(read(d+4),6*polygons),
    matrix=words(cpu.state.AR7.value,12),view=words(read(0x1120b),12),
    trig_constants={read(0x11174),read(0x11175),read(0x11176),read(0x1117b)},
    lod_context={read(0x19731),read(0x1b4bd),read(0x1d0af),read(0x1b4c1),read(0x1b4c2),read(0x1b4c3),read(0x1b4c4),read(0x1122a),read(0x1122b),read(0x1122c),read(0x1122d),read(0x1122e),read(0x1122f)},lod_index=read(0x1b718),
    origin_x=read(0x11230),radius=read(0x1b70c),
    near=read(0x11222),far=read(0x1b725),extra_flags=read(0x1b71e),path=0}
  end))
  taps[#taps+1]=s:install_read_tap(0x11230,0x11230,'offroad_model_path',guard(function(o,d,m)
   if not current then return end
   local pc=cpu.state.PC.value
   if pc==0x1e03 or pc==0x1e3b or pc==0x1e60 then current.path=pc end
  end))
  taps[#taps+1]=s:install_read_tap(0x1b704,0x1b704,'offroad_model_projected',guard(function(o,d,m)
   if cpu.state.PC.value~=0x1f67 or not current then return end
   assert(current.object==cpu.state.AR6.value and not current.projected,'Off Road model owner')
   assert(current.path~=0 and cpu.state.AR2.value==current.lod_words[5],'Off Road projection dispatch')
   current.end_frame=frame;current.projected=words(current.vertex_buffer,3*current.vertices)
   local obj=current.object_words;local values={}
   for i=0,current.polygons-1 do values[#values+1]=read(obj[18]+(current.polygon_words[1+6*i]>>16)) end
   current.palette_words=values;emit(current);projected_count=projected_count+1
  end))
  taps[#taps+1]=s:install_write_tap(0x980040,0x980040,'offroad_model_page',guard(function(o,d,m)page=d end))
  taps[#taps+1]=s:install_write_tap(0x600000,0x600000,'offroad_model_dma',guard(function(o,d,m)
   if #dma<16 then dma[#dma+1]=d&65535 end
  end))
  taps[#taps+1]=s:install_read_tap(0x980083,0x980083,'offroad_model_draw',guard(function(o,d,m)
   local pc=cpu.state.PC.value
   if (pc==0x1fb0 or pc==0x1fed) and current and current.projected then
    assert(#dma>=15,'Off Road incomplete DMA')
    draws:write(string.format('%d,%d,%d,%d,%d,%d',frame,current.call,current.object,current.model,pc,page))
    for i=1,16 do draws:write(','..(dma[i] or 0)) end;draws:write('\n');draw_count=draw_count+1
   end
   dma={}
  end))
 elseif n==last+1 then
  complete=not failure and projected_count>0 and draw_count>0;close();assert(complete,'No complete Off Road model evidence')
 end
end
