-- Independent bounded CPU scene/list/model boundary journal. Raw operands local.
-- CRUISN_EXOTICA_SCENE_WINDOWS=3498:3502; at most240 selected frames.
local cpu=manager.machine.devices[':maincpu'];local space=cpu.spaces.program
local ram=manager.machine.memory.shares[':ram_base'];local screen=manager.machine.screens[':screen']
assert(manager.machine.system.name=='crusnexo' and space.address_mask==0xffffff)
local windows,total={},0
for piece in ((os.getenv('CRUISN_EXOTICA_SCENE_WINDOWS') or '3498:3502')..','):gmatch('(.-),') do
 local a,b=piece:match('^(%d+):(%d+)$');a,b=tonumber(a),tonumber(b)
 assert(a and b and a>=1800 and b>=a and b<=16000 and (#windows==0 or a>windows[#windows][2]))
 total=total+b-a+1;assert(total<=240);windows[#windows+1]={a,b}
end
assert(#windows>0)
local taps,out,frame,busy,failure,count,complete={},nil,0,false,nil,0,false
local function selected()for _,w in ipairs(windows) do if frame>=w[1] and frame<=w[2] then return true end end;return false end
local function read(p)
 p=p&0xffffff;assert(p<0x40000 or p>=0xa00000,'scene operand outside RAM/ROM')
 return p<0x40000 and ram:read_u32(p*4) or space:read_u32(p)
end
local function emit(kind,address,data)
 count=count+1;assert(count<=65536,'scene event budget')
 assert(out:write(string.format('{"kind":"%s","frame":%u,"time":%.12f,"pc":%u,"address":%u,"data":%u,"object":%u,"flags":%u,"camera":[%u,%u,%u],"sky":%u}\n',
  kind,screen:frame_number(),emu.time(),cpu.state.PC.value,address,data,cpu.state.AR7.value,cpu.state.R6.value,
  read(0xfeb),read(0xfec),read(0xfed),read(0x103e))))
end
local function guard(fn)return function(...)
 if not out or busy or failure or not selected() then return end
 busy=true;local ok,e=pcall(fn,...);busy=false;if not ok then failure=tostring(e) end
end end
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if out then
  assert(out:close());out=nil
  local f=assert(io.open('exotica-scene-events.json','w'))
  assert(f:write(string.format('{"schema":1,"events":%u,"complete":%s}\n',count,tostring(complete and not failure))))
  assert(f:close())
 end
end
cruisn_exotica_scene_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 if n==windows[1][1] then
  for p,v in pairs({[0x67f5]=0x15200ff2,[0x681f]=0x082fbbb5,[0x6835]=0x082fbbb9,[0x6963]=0x0820b47d,[0x6c91]=0x0820b47d}) do
   assert(read(p)==v,'scene boundary signature')
  end
  out=assert(io.open('exotica-scene-events.jsonl','w'));out:setvbuf('full',65536)
  taps[#taps+1]=space:install_write_tap(0xff2,0xff2,'scene_boundary_begin',guard(function(o,d,m)
   if cpu.state.PC.value==0x67f6 then emit('begin',o,d) end
  end))
  taps[#taps+1]=space:install_read_tap(0xbbb5,0xbbb9,'scene_boundary_lists',guard(function(o,d,m)
   if o==0xbbb5 and cpu.state.PC.value==0x6820 then emit('static',o,d)
   elseif o==0xbbb9 and cpu.state.PC.value==0x6836 then emit('end',o,d) end
  end))
  taps[#taps+1]=space:install_read_tap(0xb47d,0xb47d,'scene_boundary_model',guard(function(o,d,m)
   if cpu.state.PC.value==0x6964 then emit('model',o,d)
   elseif cpu.state.PC.value==0x6c92 then emit('special',o,d) end
  end))
 elseif n==windows[#windows][2]+1 then
  assert(count>0,'empty scene boundary capture');complete=true;close()
 end
end
