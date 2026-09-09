-- Bounded read-only USA 4.5 model oracle. Raw game operands stay LOCAL.
-- Compose with usa_motion_trace.lua to verify actual ADC timing and route.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnusa')
local first=tonumber(os.getenv('CRUISN_USA_MODEL_FIRST') or '3500')
local last=tonumber(os.getenv('CRUISN_USA_MODEL_LAST') or '3550')
assert(first and last and first%1==0 and last%1==0 and first>=1800 and last>=first
 and last-first<=120,'invalid USA model capture interval')
local frame,taps,out,draws,current,serial,failure,busy=0,{},nil,nil,nil,0,nil,false
local projected_count,draw_count,complete=0,0,false
local dma,page={},0
local function words(p,n)
 assert(n>=0 and n<=8192 and (p>=0 and p+n<=0x20000 or p>=0x809800 and p+n<=0x80a000 or p>=0xc00000 and p+n<=0x1000000),'unmapped model read')
 assert(p+n<=0xc93e or p>0xc93f,'model probe must not invoke USA speedup handler')
 local a={};for i=0,n-1 do a[#a+1]=s:read_u32(p+i) end;return a
end
local function guard(fn) return function(...)
 if busy or failure then return end;busy=true
 local ok,e=pcall(fn,...);busy=false;if not ok then failure=tostring(e) end
end end
local function emit(r)
 local keys={};for k in pairs(r) do keys[#keys+1]=k end;table.sort(keys);local parts={}
 for _,k in ipairs(keys) do local v=r[k];parts[#parts+1]='"'..k..'":'..(type(v)=='table' and '['..table.concat(v,',')..']' or tostring(v)) end
 out:write('{'..table.concat(parts,',')..'}\n')
end
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if out then
  out:close();draws:close();out=nil
  local receipt=assert(io.open('usa-model-capture.json','w'))
  receipt:write(string.format('{"schema":1,"first":%d,"last":%d,"started":%d,"projected":%d,"draws":%d,"complete":%s}\n',
   first,last,serial,projected_count,draw_count,complete and 'true' or 'false'))
  receipt:close()
 end
end
cruisn_usa_model_stop=emu.add_machine_stop_notifier(close)
return function(n)
 assert(not failure,failure);frame=n
 if n==first then
  for p,v in pairs({[0x129]=0x085b2101,[0x12c]=0x082b004f,[0x140]=0x64000162,[0x15d]=0x24c00182,
   [0x49a]=0x0831004f,[0x188]=0x085b2101,[0x18b]=0x082b004f,[0x1bb]=0x6a00ffa7,[0x163]=0x0e330000,[0x28d]=0x0846000e,[0x29a]=0x08330062,[0x477]=0x08422102,[0x48f]=0x08200083}) do
   assert(s:read_u32(p)==v,string.format('USA model guard %x',p))
  end
  out=assert(io.open('usa-model-transform.jsonl','w'));out:setvbuf('full',65536)
  draws=assert(io.open('usa-model-draws.csv','w'));draws:setvbuf('full',65536)
  draws:write('frame,call,object,model,pc,page,flags,palette,x0,y0,x1,y1,x2,y2,x3,y3,uv0,uv1,uv2,uv3,texture,word15\n')
  local f=assert(io.open('usa-model-reciprocals.bin','wb'));local base=s:read_u32(0x52)
  assert(base==0xb2b3,'USA reciprocal layout mismatch')
  for i=-80,4999 do f:write(string.pack('<I4',words(base+i,1)[1])) end;f:close()
  page=s:read_u32(0x980040)
  taps[#taps+1]=s:install_read_tap(0x45,0x45,'usa_model_owner',guard(function(o,d,m)
   if cpu.state.PC.value==0x9e then current=nil end
  end))
  taps[#taps+1]=s:install_read_tap(0x4f,0x4f,'usa_model_start',guard(function(o,d,m)
   if cpu.state.PC.value~=0x12d and cpu.state.PC.value~=0x18c then return end
   local compact=cpu.state.PC.value==0x18c
   local id=cpu.state.AR0.value;local model=cpu.state.AR1.value-2
   local header=words(cpu.state.SP.value,1)[1];local vertices=(header&255)+1;local polygons=(header>>16)+1
   assert(vertices<=256 and polygons<=1024 and s:read_u32(model+1)==header,'USA model header/count mismatch')
   serial=serial+1
   assert(serial<=100000,'USA model capture count bound')
   assert(model>=0xc00000,'USA static model outside ROM')
   current={schema=2,call=serial,frame=frame,object=id,model=model,object_words=words(id,32),vertices=vertices,polygons=polygons,
    model_words=words(model,2+2*vertices+5*polygons),vertex_buffer=d,
    compact=compact and 1 or 0,matrix=words(cpu.state.AR5.value,compact and 4 or 9),camera_space=words(cpu.state.AR6.value-1,3),
    camera=words(s:read_u32(0x45),3),view=words(s:read_u32(0x47),9),fast=0,
    origin_y=compact and s:read_u32(0x54) or 0x07480000,
    billboard_full=words(s:read_u32(0x4d),9),billboard_compact=words(s:read_u32(0x4e),4),
    dispatch_mode=s:read_u32(0xc8f5),dispatch_enable=s:read_u32(0xe8a1)}
  end))
  taps[#taps+1]=s:install_read_tap(0x4f,0x4f,'usa_model_projected',guard(function(o,d,m)
   if (cpu.state.PC.value~=0x296 and cpu.state.PC.value~=0x49b) or not current then return end
   d=s:read_u32(0x62)
   assert(current.object==cpu.state.AR0.value and not current.projected,'USA model owner mismatch')
   assert(cpu.state.AR1.value==current.model+2+2*current.vertices,'USA polygon start mismatch')
   current.projected=words(current.vertex_buffer,3*current.vertices)
   current.end_frame=frame;current.palette_table=d
   current.palette_kind=(current.object_words[15]&0x400)~=0 and 1 or 0
   current.fast=(cpu.state.R0.value>1000 and cpu.state.R0.value<0x80000000 and (current.object_words[15]&0x40)==0) and 1 or 0
   local kind=current.object_words[16];local depth=current.object_words[29]
   if current.palette_kind==1 and current.polygons>50 and depth<=8000 and
       (kind==0x484 or ((kind&0xf00)>=0x100 and (kind&0xf00)<=0x200)) then current.fast=0 end
   local values={};for i=0,current.polygons-1 do
    local flags=current.model_words[3+2*current.vertices+5*i]
    values[#values+1]=current.palette_kind==1 and current.object_words[17] or words(d+(flags>>16),1)[1]
   end
   current.palette_words=values;emit(current);projected_count=projected_count+1
  end))
  taps[#taps+1]=s:install_write_tap(0x980040,0x980040,'usa_model_page',guard(function(o,d,m)page=d end))
  taps[#taps+1]=s:install_write_tap(0x600000,0x600000,'usa_model_dma',guard(function(o,d,m)
   if #dma<16 then dma[#dma+1]=d&65535 end
  end))
  taps[#taps+1]=s:install_read_tap(0x980083,0x980083,'usa_model_draw',guard(function(o,d,m)
   local pc=cpu.state.PC.value
   if (pc==0x490 or pc==0x54f) and current and current.projected then
    assert(current.object==cpu.state.AR0.value and #dma>=15,'USA draw owner/DMA mismatch')
    draws:write(string.format('%d,%d,%d,%d,%d,%d',frame,current.call,current.object,current.model,pc,page))
    for i=1,16 do draws:write(','..(dma[i] or 0)) end;draws:write('\n');draw_count=draw_count+1
   end
   dma={}
  end))
 elseif n==last+1 then
  complete=not failure and projected_count>0 and draw_count>0;close()
  assert(complete,'no complete USA model evidence')
 end
end
