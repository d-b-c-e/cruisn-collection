-- Read-only World road-codec evidence. Raw resources must remain local.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24')
local first=tonumber(os.getenv('CRUISN_ROAD_FIRST') or '4400')
local last=tonumber(os.getenv('CRUISN_ROAD_LAST') or '4500')
assert(first and last and first>=1 and last>=first and last-first<=1200,'bounded road interval required')
local frame,taps,out,draws,current,serial,fail=0,{},nil,nil,nil,0,nil
local pending,page,projected_count,draw_count,unmatched={},0,0,0,0
local function words(p,n)
 assert(n>=0 and n<=4096 and (p>=0 and p+n<=0x20000 or p>=0x809800 and p+n<=0x80a000 or p>=0xc00000 and p+n<=0x1000000),'unmapped road read')
 local a={};for i=0,n-1 do a[#a+1]=s:read_u32(p+i) end;return a
end
local function emit(r)
 local keys={};for k in pairs(r) do keys[#keys+1]=k end;table.sort(keys);local parts={}
 for _,k in ipairs(keys) do local v=r[k];parts[#parts+1]='"'..k..'":'..(type(v)=='table' and '['..table.concat(v,',')..']' or tostring(v)) end
 out:write('{'..table.concat(parts,',')..'}\n')
end
local function guard(fn)return function(...)if fail then return end;local ok,why=pcall(fn,...);if not ok then fail=tostring(why) end end end
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if out then
  out:close();draws:close();out=nil
  local f=assert(io.open('world-road-summary.json','w'))
  f:write(string.format('{"starts":%d,"projected":%d,"draws":%d,"unmatched_draws":%d,"first":%d,"last":%d,"completed":%s}\n',serial,projected_count,draw_count,unmatched,first,last,tostring(frame>=last+1 and not fail)))
  f:close()
 end
end
cruisn_road_stop=emu.add_machine_stop_notifier(close)
return function(n)
 if fail then error(fail) end;frame=n
 if n==first then
  for p,v in pairs({[0x62c]=0x04a1d4c0,[0x635]=0x152fd4bf,[0x638]=0x08412101,[0x641]=0x082b0049,[0x677]=0x04f21387,[0x67d]=0x24c00182,[0x683]=0x6a20fb9d,[0x241]=0x082ed4bf,[0x2e0]=0x082ed4bf}) do assert(s:read_u32(p)==v,'road instruction signature') end
  out=assert(io.open('world-road-transform.jsonl','w'));draws=assert(io.open('world-road-draws.csv','w'))
  draws:write('frame,call,object,model,pc,page,flags,palette,x0,y0,x1,y1,x2,y2,x3,y3,uv0,uv1,uv2,uv3,texture,word15\n')
  local f=assert(io.open('world-road-reciprocals.bin','wb'));local base=s:read_u32(0x4d)
  for i=-80,4999 do f:write(string.pack('<I4',s:read_u32(base+i))) end;f:close()
  page=s:read_u32(0x980040)
  taps[#taps+1]=s:install_read_tap(0x40,0x40,'road_owner',guard(function(o,d,m)if cpu.state.PC.value==0xa1 then current=nil end end))
  taps[#taps+1]=s:install_read_tap(0x49,0x49,'road_begin',guard(function(o,d,m)
   if cpu.state.PC.value~=0x642 then return end
   local id=cpu.state.AR0.value;local obj=words(id,32);assert(obj[15]&0x801==1,'unexpected road flags')
   local model=obj[14];local selected=s:read_u32(0xd4bf)
   local header=s:read_u32(cpu.state.SP.value);local vertices=cpu.state.RC.value+1;local polygons=(header>>18)+1
   assert(vertices==header&255 and vertices>0 and vertices<=256 and polygons<=1024,'road counts')
   assert(cpu.state.AR1.value==model+3,'road vertex start')
   local mw={s:read_u32(model),s:read_u32(selected+1),header}
   for _,v in ipairs(words(model+3,vertices*2)) do mw[#mw+1]=v end
   for _,v in ipairs(words(cpu.state.AR7.value,polygons*2)) do mw[#mw+1]=v end
   serial=serial+1
   local table=s:read_u32(0x624);local slot=((obj[16]&0xf000)>>12)-1
   assert(slot>=0 and slot<15,'unsupported road template slot')
   local template=words(table+slot,1)[1]
   current={call=serial,frame=frame,object=id,model=selected,original_model=model,object_words=obj,
    vertex_buffer=d,vertices=vertices,input_vertices=vertices,polygons=polygons,fast=0,
    lod_threshold=s:read_u32(0xd4c0),template_table=table,template_slot=slot,template_model=template,
    original_header=s:read_u32(model+2),model_words=mw,material_words=words(mw[2],polygons*3),
    camera=words(s:read_u32(0x41),3),view=words(s:read_u32(0x43),9),
    matrix=words(cpu.state.AR5.value,9),camera_space=words(cpu.state.AR6.value-1,5)}
  end))
  taps[#taps+1]=s:install_read_tap(0xd4bf,0xd4bf,'road_projected',guard(function(o,d,m)
   local pc=cpu.state.PC.value;if pc~=0x242 and pc~=0x2e1 then return end
   if not current then return end
   assert(current.model==d,'road selected model changed')
   local id=pc==0x2e1 and s:read_u32(cpu.state.SP.value) or cpu.state.AR0.value
   assert(current.object==id and not current.projected,'road owner/duplicate')
   current.projected=words(current.vertex_buffer,3*current.vertices);current.end_pc=pc;current.end_frame=frame;current.page=page;emit(current);projected_count=projected_count+1
  end))
  taps[#taps+1]=s:install_write_tap(0x980040,0x980040,'road_page',guard(function(o,d,m)page=d end))
  taps[#taps+1]=s:install_write_tap(0x600000,0x600000,'road_dma',guard(function(o,d,m)if #pending<16 then pending[#pending+1]=d&65535 end end))
  taps[#taps+1]=s:install_read_tap(0x980083,0x980083,'road_draw',guard(function(o,d,m)
   local pc=cpu.state.PC.value
   if #pending>=15 and (pc==0x289 or pc==0x2ca or pc==0x333) then
    local id=pc==0x333 and s:read_u32(cpu.state.SP.value) or cpu.state.AR0.value
    if current and current.object==id and current.projected then
     draws:write(string.format('%d,%d,%d,%d,%d,%d',frame,current.call,id,current.model,pc,page))
     for i=1,16 do draws:write(','..(pending[i] or 0)) end;draws:write('\n');draw_count=draw_count+1
    else unmatched=unmatched+1
    end
   end;pending={}
  end))
 elseif n==last+1 then close();assert(serial>0,'no road evidence') end
end
