-- Bounded USA pending scene/layout oracle. Raw geometry/materials stay LOCAL.
-- Use the RAM share: address-space reads at PC81 would retrigger native hooks.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local ram=assert(manager.machine.memory.shares[':ram_base'])
assert(manager.machine.system.name=='crusnusa')
local first=tonumber(os.getenv('CRUISN_USA_SCENE_FIRST') or '3500')
local last=tonumber(os.getenv('CRUISN_USA_SCENE_LAST') or '5000')
local step=tonumber(os.getenv('CRUISN_USA_SCENE_STEP') or '500')
assert(first and last and step and first%1==0 and last%1==0 and step%1==0
 and first>=1800 and last>=first and last-first<=3000 and step>=100,'invalid scene bounds')
local frame,scene,taps,busy,failure,next_capture=0,0,{},false,nil,first
local phases,draw_count,phase_count=nil,0,0
local snapshot_count=0
local function allowed(p,n)
 return n>=0 and n<=8192 and (p>=0 and p+n<=0x20000 or p>=0x809800 and p+n<=0x80a000 or p>=0xc00000 and p+n<=0x1000000)
  and (p+n<=0xc93e or p>0xc93f)
end
local function read(p)
 assert(allowed(p,1),'unsafe scene read')
 if p<0x20000 then return ram:read_u32(4*p)end
 return s:read_u32(p)
end
local function guard(fn)return function(...)
 if busy or failure then return end;busy=true
 local ok,reason=pcall(fn,...);busy=false;if not ok then failure=tostring(reason)end
end end
local function close()
 for _,tap in ipairs(taps)do tap:remove()end;taps={}
 if phases then phases:close();phases=nil end
end
cruisn_usa_scene_stop=emu.add_machine_stop_notifier(close)
local function snapshot()
 local memory={};local function get(p)local v=read(p);memory[p]=v;return v end
 local function words(p,n)
  assert(allowed(p,n),'unsafe scene span');local a={};for i=0,n-1 do a[#a+1]=get(p+i)end;return a
 end
 for p=0x40,0x55 do get(p)end
 get(0x62);get(0xc8f5);get(0xe8a1)
 words(get(0x45),3);words(get(0x47),9);words(get(0x4d),9);words(get(0x4e),4)
 words(get(0x52)-80,5080)
 local objects,models={},{}
 for _,slot in ipairs({0x43,0x40,0x42,0x44,0x41})do
  local head=get(slot);local id=get(head);local seen={};local count=0
  while id~=0 do
   assert(id>=0x1000 and id+32<=0x20000 and not seen[id] and count<2048,'bad list')
   seen[id]=true;count=count+1
   local o=words(id,32);objects[id]=o;id=o[1]
  end
 end
 for _,o in pairs(objects)do
  for _,i in ipairs({14,25,26})do
   local p=o[i]
   if p>=0xc00000 and p+2<=0x1000000 then
    local header=get(p+1);local vertices=(header&255)+1;local polys=(header>>16)+1
    if polys<=1024 and allowed(p,2+2*vertices+5*polys)then
     if not models[p]then models[p]=words(p,2+2*vertices+5*polys)end
     local model=models[p]
     if (o[15]&0x400)==0 then
      local table=get(0x62)
      for poly=0,polys-1 do local flags=model[3+2*vertices+5*poly];get(table+(flags>>16))end
     end
    end
   end
  end
 end
 local addresses={};for p in pairs(memory)do addresses[#addresses+1]=p end;table.sort(addresses)
 local file=assert(io.open(string.format('usa-scene-%05d.json',frame),'w'))
 file:write(string.format('{"frame":%d,"native_frame":%d,"time":"%.12f","page":%d,"scene":%d,"draws_before_main":%d,"memory":[',frame,manager.machine.screens[':screen']:frame_number(),emu.time(),s:read_u32(0x980040),scene,draw_count))
 for i,p in ipairs(addresses)do if i>1 then file:write(',')end;file:write(string.format('[%d,%d]',p,memory[p]))end
 file:write(']}\n');file:close();snapshot_count=snapshot_count+1
end
return function(n)
 frame=n;assert(not failure,failure)
 if n==first then
  for p,v in pairs({[0x7d]=0x08280043,[0x7e]=0x62000166,[0x80]=0x08280040,[0x81]=0x62000166,
   [0x83]=0x08280042,[0x84]=0x62000166,[0x86]=0x08280044,[0x87]=0x62000166,[0x166]=0x0840c000})do
   assert(read(p)==v,'scene code signature')
  end
  phases=assert(io.open('usa-scene-phases.csv','w'));phases:setvbuf('full',65536)
  phases:write('frame,scene,slot,head,previous_draws\n')
  taps[#taps+1]=s:install_read_tap(0x980083,0x980083,'usa_scene_dma_count',guard(function()draw_count=draw_count+1 end))
  taps[#taps+1]=s:install_read_tap(0x40,0x44,'usa_scene_lists',guard(function(p,d,m)
   local pc=cpu.state.PC.value
   if not (p==0x43 and pc==0x7e or p==0x40 and pc==0x81 or p==0x42 and pc==0x84 or p==0x44 and pc==0x87)then return end
   if p==0x43 then scene=scene+1;draw_count=0 end
   phases:write(string.format('%d,%d,%d,%d,%d\n',frame,scene,p,d,draw_count));phase_count=phase_count+1
   if p==0x40 and frame>=next_capture then snapshot();next_capture=next_capture+step end
  end))
 elseif n==last+1 then close();assert(snapshot_count>=math.ceil((last-first)/step) and phase_count>0,'incomplete scene capture')end
end
