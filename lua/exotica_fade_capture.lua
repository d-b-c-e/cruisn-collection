-- SPDX-License-Identifier: BSD-3-Clause
-- Bounded original Exotica2.4 fade updates; read-only. Raw operands stay local.
local cpu=manager.machine.devices[':maincpu'];local space=cpu.spaces.program
local screen=manager.machine.screens[':screen'];local ram=manager.machine.memory.shares[':ram_base']
assert(manager.machine.system.name=='crusnexo')
local taps={};local frame=0;local count=0
local out=nil;local failure=nil;local pending=nil;local complete=false;local windows={};local total=0
local spec=os.getenv('CRUISN_EXOTICA_FADE_WINDOWS') or '3500:3550,4650:4750,5400:5450'
for piece in (spec..','):gmatch('(.-),') do
 local a,b=piece:match('^(%d+):(%d+)$');a,b=tonumber(a),tonumber(b)
 assert(a and b and a>=1800 and b>=a and b<=16000 and (#windows==0 or a>windows[#windows][2]),'Exotica fade windows')
 total=total+b-a+1;assert(total<=240 and #windows<16,'Exotica fade frame budget');windows[#windows+1]={a,b}
end
assert(#windows>0,'empty Exotica fade windows')
local function read(p) assert(p>=0 and p<0x40000);return ram:read_u32(p*4) end
local function guard(fn) return function(o,d,m) if failure then return end;local ok,e=pcall(fn,o,d,m);if not ok then failure=e end end end
local function finish(flags)
 assert(pending and pending.actual,'missing original fade write')
 count=count+1;assert(count<=8192,'fade capture budget')
 local p=pending
 out:write(string.format('{"id":%d,"frame":%d,"native_frame":%d,"time":%.17g,"object":%d,"increment":%d,"before":%d,"flags_before":%d,"actual":%d,"flags_after":%d}\n',count,frame,screen:frame_number(),emu.time(),p.object,p.increment,p.before,p.flags,p.actual,flags))
 pending=nil
end
local function detach()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if pending then failure=failure or 'unfinished fade transaction';pending=nil end
end
local function attach()
 taps[#taps+1]=space:install_read_tap(0x588,0x588,'exotica_fade_increment',guard(function(o,d,m)
  if cpu.state.PC.value~=0xb73e then return end
  assert(not pending,'overlapping fade updates')
  local object=cpu.state.AR0.value;assert(object>=0x1000 and object+32<0x40000)
  pending={object=object,increment=d,before=cpu.state.R2.value,flags=cpu.state.R6.value}
 end))
 taps[#taps+1]=space:install_write_tap(0x1000,0x3ffff,'exotica_fade_result',guard(function(o,d,m)
  local pc=cpu.state.PC.value
  if pc==0xb749 then
   assert(pending and o==pending.object+0x10,'fade word owner')
   pending.actual=d
   if (((pending.before>>16)&255)+pending.increment)<247 then finish(pending.flags) end
  elseif pc==0xb74e and pending then
   assert(o==pending.object+0xf and pending.actual,'fade flag owner');finish(d)
  end
 end))
end
local function close()
 if out then
  detach();out:close();out=nil
  local r=assert(io.open('exotica-fade-capture.json','w'))
  r:write(string.format('{"complete":%s,"events":%d,"error":%s,"windows":[',tostring(complete and not failure),count,failure and string.format('%q',tostring(failure)) or 'null'))
  for i,w in ipairs(windows) do r:write(string.format('%s[%d,%d]',i>1 and ',' or '',w[1],w[2])) end
  r:write(']}\n');r:close()
 end
end
exotica_fade_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 if n==windows[1][1] then
  for p,v in pairs({[0xb73d]=0x02200588,[0xb748]=0x15410010,[0xb74d]=0x1546000f,[0xbbb1]=0x04000000}) do assert(read(p)==v,'fade signature') end
  out=assert(io.open('exotica-fade-events.jsonl','w'));out:setvbuf('full',65536)
 end
 for _,w in ipairs(windows) do if n==w[1] then attach() elseif n==w[2]+1 then detach() end end
 if n==windows[#windows][2]+1 then complete=true;close() end
end
