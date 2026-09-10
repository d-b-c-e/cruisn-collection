-- Bounded, read-only Exotica2.4 transform and actual model-command capture.
-- CRUISN_EXOTICA_MODEL_WINDOWS=3500:3525,4650:4750,5400:5420 (max240 frames).
-- Raw operands stay LOCAL. This does not capture/verify Zeus model geometry.
local cpu=manager.machine.devices[':maincpu'];local space=cpu.spaces.program
local ram=manager.machine.memory.shares[':ram_base'];local screen=manager.machine.screens[':screen']
assert(manager.machine.system.name=='crusnexo')
local windows,total={},0
local spec=os.getenv('CRUISN_EXOTICA_MODEL_WINDOWS') or '3500:3525,4650:4750,5400:5420'
for piece in (spec..','):gmatch('(.-),') do
 local a,b=piece:match('^(%d+):(%d+)$');a,b=tonumber(a),tonumber(b)
 assert(a and b and a>=1800 and b>=a and b<=16000 and (#windows==0 or a>windows[#windows][2]),'Exotica model windows')
 total=total+b-a+1;assert(total<=240);windows[#windows+1]={a,b}
end
assert(#windows>0)
local function selected(n)for _,w in ipairs(windows) do if n>=w[1] and n<=w[2] then return true end end;return false end
local frame,busy,failure,serial,emitted,complete=0,false,nil,0,0,false
local taps,out,emissions,previous={},nil,nil,nil
local function read(p)
 assert(p>=0 and p%1==0 and (p<0x40000 or p>=0x87fe00 and p<0x880000 or p>=0xa00000 and p<0x1000000),'unmapped Exotica operand')
 return p<0x40000 and ram:read_u32(p*4) or space:read_u32(p)
end
local function words(p,n)local a={};assert(n>=0 and n<=64);for i=0,n-1 do a[#a+1]=read(p+i) end;return a end
local function emit(file,r)
 local keys={};for k in pairs(r) do keys[#keys+1]=k end;table.sort(keys);local a={}
 for _,k in ipairs(keys) do local v=r[k];a[#a+1]='"'..k..'":'..(type(v)=='table' and '['..table.concat(v,',')..']' or tostring(v)) end
 assert(file:write('{'..table.concat(a,',')..'}\n'))
end
local function guard(fn)return function(...)
 if busy or failure or not selected(frame) then return end
 busy=true;local ok,e=pcall(fn,...);busy=false;if not ok then failure=tostring(e) end
end end
local function ring_words(ring,n)
 assert(ring>=0x30000 and ring<0x32000);local result={}
 for i=-n,-1 do result[#result+1]=read(0x30000+((ring-0x30000+i)%0x2000)) end;return result
end
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if out then
  out:close();emissions:close();out=nil;emissions=nil
  local f=assert(io.open('exotica-model-capture.json','w'))
  f:write(string.format('{"schema":1,"first":%d,"last":%d,"window_frames":%d,"calls":%d,"emissions":%d,"complete":%s}\n',windows[1][1],windows[#windows][2],total,serial,emitted,tostring(complete)));f:close()
 end
end
cruisn_exotica_model_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 if n==windows[1][1] then
  for p,v in pairs({[0x689d]=0x07200ff9,[0x6961]=0x08480711,[0x6963]=0x0820b47d,
   [0x6968]=0x04e261a8,[0x696a]=0x08410004,[0x696f]=0x152d046e,
   [0xb47d]=0x24860000,[0xb479]=0x07000000,[0xb48b]=0x16000000,
   [0x67bf]=0x87ff35,[0x67c0]=0x87ff3e,[0x67c1]=0x87ff4a,[0x67c3]=0x87ff48,
   [0x67d9]=0x80002,[0xbbaa]=0x80000}) do assert(read(p)==v,'Exotica transform signature') end
  out=assert(io.open('exotica-models.jsonl','w'));out:setvbuf('full',65536)
  emissions=assert(io.open('exotica-emissions.jsonl','w'));emissions:setvbuf('full',65536)
  taps[#taps+1]=space:install_read_tap(0xff9,0xff9,'exotica_transform_cache',guard(function(o,d,m)
   if cpu.state.PC.value==0x689e then previous={object=cpu.state.AR7.value,alpha=d,frame=frame} end
  end))
  taps[#taps+1]=space:install_read_tap(0xb47d,0xb47d,'exotica_transform_ready',guard(function(o,d,m)
   if cpu.state.PC.value~=0x6964 then return end
   serial=serial+1;assert(serial<=65536,'Exotica model budget')
   local object=cpu.state.AR7.value;assert(object>=0x1000 and object+0x94<=0x40000)
   assert(previous and previous.object==object and previous.frame==frame,'Exotica matrix-cache context')
   local descriptor=cpu.state.AR0.value;local obj=words(object,32);local flags=cpu.state.R6.value
   assert(obj[18]==descriptor,'Exotica descriptor owner')
   local primary=words(descriptor,5);local chosen=descriptor;local depth=obj[21]
   if depth>=0x80000000 then depth=depth-0x100000000 end
   if primary[1]~=0 and depth>25000 then chosen=primary[1] end
   local ring=cpu.state.AR5.value
   emit(out,{schema=1,id=serial,frame=frame,native_frame=screen:frame_number(),time=emu.time(),pc=cpu.state.PC.value,
    object=object,object_words=obj,flags=flags,descriptor=descriptor,primary=primary,selected=chosen,
    metadata=words(chosen,5),view=words(read(0x67bf),9),camera=words(0xfeb,3),prepared=words(read(0x67c1),9),
    rotation=words(object+((flags&0x80)~=0 and 0x8b or 5),9),translation=words(read(0x67c3)-1,3),alternate=words(read(0x67c0),9),
    matrix_cursor=cpu.state.AR1.value,scale=read(0x67db),ring=ring,preceding=ring_words(ring,16),
    previous_alpha=previous.alpha,matrix_update=read(0xffa)})
   previous=nil
  end))
  taps[#taps+1]=space:install_write_tap(0x046e,0x046e,'exotica_model_emission',guard(function(o,d,m)
   if cpu.state.PC.value~=0x6970 then return end
   emitted=emitted+1;assert(emitted<=65536)
   local ring=cpu.state.AR5.value
   emit(emissions,{id=serial,frame=frame,native_frame=screen:frame_number(),time=emu.time(),pc=cpu.state.PC.value,
    object=cpu.state.AR7.value,selected=cpu.state.AR0.value,ring=ring,packet=ring_words(ring,2)})
  end))
 elseif n==windows[#windows][2]+1 then
  assert(serial>0 and emitted>0,'empty Exotica capture');complete=true;close()
 end
end
