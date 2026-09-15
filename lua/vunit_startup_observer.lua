-- SPDX-License-Identifier: BSD-3-Clause
-- Read-only first-scene evidence; no renderer enablement or guest mutation.
local cpu=manager.machine.devices[':maincpu'];local space=cpu.spaces.program
local ram=assert(manager.machine.memory.shares[':ram_base'])
local rom=manager.machine.system.name
local profiles={
 crusnusa={address=0x40,pc=0x81,words={0x40,0x41,0x45,0x47,0x52,0x62,0xa12e,0xe4a5,0xe49d,0xe4a4}},
 crusnwld24={address=0x61ee,pc=0x6a,words={0x61ee,0x61ec,0xd575,0xd5a5,0xd5a1,0xd58c,0x4151,0x4150}},
 crusnwld={address=0x658f,pc=0x6a,words={0x658f,0x658d,0xd56f,0xd59f,0xd59b,0xd586,0x4121,0x4120}},
 offroadc={address=0x111f4,pc=0x1bf9,words={0x111f4,0x111ee,0x1120b,0x1b4b4,0x1b4cc,0x1b4b5,0x1b4b7,0x1b4ba}},
}
local profile=assert(profiles[rom],'unsupported V-Unit startup profile')
local last=tonumber(os.getenv('CRUISN_STARTUP_LAST') or '2099')
assert(last and last%1==0 and last>=1 and last<=3500 and ram.size==0x80000,'invalid startup observation bounds')
local frame,count,saved,busy,failure,tap,out=0,0,0,false,nil,nil,nil
local wanted,budget={},0
local requested=os.getenv('CRUISN_STARTUP_SNAPSHOTS') or '1,2,16'
assert(requested:match('^%d[%d,]*%d$') and not requested:find(',,') or requested:match('^%d$'),'invalid startup snapshot list')
for token in requested:gmatch('[^,]+')do
 local sequence=tonumber(token)
 assert(sequence and sequence%1==0 and sequence>=1 and sequence<=4096 and not wanted[sequence],'invalid startup snapshot sequence')
 wanted[sequence]=true;budget=budget+1
end
assert(budget>=1 and budget<=8,'startup snapshot budget exceeded')
local function read(p)assert(p>=0 and p<0x20000);return ram:read_u32(4*p)end
local function dump(path,n,fn)
 local file=assert(io.open(path,'wb'));local chunk={}
 for i=0,n-1 do
  chunk[#chunk+1]=string.pack('<I4',fn(i))
  if #chunk==1024 then assert(file:write(table.concat(chunk)));chunk={}end
 end
 if #chunk>0 then assert(file:write(table.concat(chunk)))end
 assert(file:close())
end
local function close()
 if tap then tap:remove();tap=nil end
 if out then assert(out:close());out=nil end
end
cruisn_startup_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 if n==1 then
  out=assert(io.open('vunit-startup-scenes.csv','w'));out:setvbuf('full',65536)
  assert(out:write('sequence,frame,native_frame,time,pc,value,mask,snapshot'))
  for _,p in ipairs(profile.words)do assert(out:write(string.format(',w%05x',p)))end
  assert(out:write('\n'))
  tap=space:install_read_tap(profile.address,profile.address,'vunit_startup_scene',function(o,d,m)
   if busy or failure or cpu.state.PC.value~=profile.pc then return end
   busy=true
   local ok,reason=pcall(function()
    count=count+1;assert(count<=4096,'startup scene budget exceeded')
    assert(out:write(string.format('%d,%d,%d,%.12f,%x,%x,%x,%d',count,frame,
     manager.machine.screens[':screen']:frame_number(),emu.time(),profile.pc,d,m,wanted[count] and 1 or 0)))
    for _,p in ipairs(profile.words)do assert(out:write(string.format(',%08x',read(p))))end
    assert(out:write('\n'))
    if wanted[count] then
     local stem=string.format('vunit-startup-%02d',count)
     dump(stem..'-ram.bin',0x20000,read)
     -- Fast RAM lies outside the cycle-eating ordinary RAM handlers.
     dump(stem..'-fast.bin',0x800,function(p)return space:read_u32(0x809800+p)end)
     saved=saved+1
    end
   end)
   busy=false;if not ok then failure=tostring(reason)end
  end)
 end
 if n==last+1 then
  close();assert(count>0 and saved==budget,'startup observation did not reach required scene snapshots')
  print(string.format('VUNIT_STARTUP_OBSERVED rom=%s scenes=%d snapshots=%d',rom,count,saved))
 end
end
