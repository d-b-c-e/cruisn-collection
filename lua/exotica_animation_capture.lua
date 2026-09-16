-- SPDX-License-Identifier: BSD-3-Clause
-- Read-only Exotica2.4 model-animation updates; no allocation, RNG or guest writes.
local cpu=manager.machine.devices[':maincpu'];local space=cpu.spaces.program
local ram=manager.machine.memory.shares[':ram_base']
assert(manager.machine.system.name=='crusnexo')
local first=tonumber(os.getenv('CRUISN_EXOTICA_ANIMATION_FIRST') or '7160')
local last=tonumber(os.getenv('CRUISN_EXOTICA_ANIMATION_LAST') or '7200')
assert(first and last and first%1==0 and last%1==0 and first>=1800 and last>=first and last<=16000 and last-first<200)
local taps={};local frame=0;local out=nil;local pending=nil;local failed=nil
local events=0;local complete=false;local tables={};local table_count=0
local trace_count=0
local function trace(write,o,d)
 local pc=cpu.state.PC.value
 if pc>=0xe8cb and pc<=0xe8dc and trace_count<64 then
  trace_count=trace_count+1
  assert(out:write(string.format('{"kind":2,"write":%d,"pc":%d,"offset":%d,"data":%d,"node":%d}\n',write,pc,o,d,cpu.state.AR3.value)))
 end
end
local function read(p)
 assert(p>=0 and p<0x40000 and p%1==0,'animation RAM span');return ram:read_u32(p*4)
end
local function emit(row)
 local keys={};for k in pairs(row) do keys[#keys+1]=k end;table.sort(keys)
 local fields={};for _,k in ipairs(keys) do
  local v=row[k];fields[#fields+1]='"'..k..'":'..(type(v)=='table' and '['..table.concat(v,',')..']' or tostring(v))
 end
 assert(out:write('{'..table.concat(fields,',')..'}\n'))
end
local function guarded(fn)return function(o,d,m)
 if failed then return end;local ok,e=pcall(fn,o,d,m);if not ok then failed=tostring(e) end
end end
local function finish()
 assert(pending and pending.after_remaining,'unfinished animation update')
 events=events+1;assert(events<=8192,'animation event budget')
 pending.id=events;emit(pending);pending=nil
end
local function close()
 if not out then return end
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if pending then failed=failed or 'animation transaction crosses capture boundary' end
 local ok,e=out:close();if not ok then failed=failed or tostring(e) end;out=nil
 local f=assert(io.open('exotica-animation-capture.json','w'))
 assert(f:write(string.format('{"complete":%s,"events":%d,"tables":%d,"first":%d,"last":%d,"error":%s}\n',
  tostring(complete and not failed),events,table_count,first,last,failed and string.format('%q',failed) or 'null')))
 assert(f:close())
end
cruisn_exotica_animation_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failed,failed)
 if n==first then
  for p,v in pairs({[0xe8cb]=0x08400303,[0xe8cc]=0x18600001,[0xe8cd]=0x15400303,
   [0xe8cf]=0x08400305,[0xe8d1]=0x15400303,[0xe8d2]=0x08490302,
   [0xe8d3]=0x084a2101,[0xe8d6]=0x08490304,[0xe8d8]=0x15490302,[0xe8da]=0x154a0411}) do
   assert(read(p)==v,'animation revision signature')
  end
  out=assert(io.open('exotica-animation-events.jsonl','w'));assert(out:setvbuf('full',65536))
  taps[#taps+1]=space:install_read_tap(0x1000,0x3ffff,'animation_countdown',guarded(function(o,d,m)
   trace(0,o,d)
   if cpu.state.PC.value~=0xe8cc then return end
   -- The program space also reports instruction fetches at the current PC.
   -- E8CC itself is SUBI, not a read of the node countdown.
   if o==0xe8cc then return end
   assert(not pending,'overlapping animation updates')
   local node=cpu.state.AR3.value;assert(o==node+3 and node>=0x1000 and node+6<0x40000)
   local owner=read(node+1);assert(owner>=0x1000 and owner+32<0x40000)
   local start=read(node+4);local header=read(node+5)
   if not tables[start] then
    assert(start>=0xa00000 and start<0xffff00 and table_count<32,'animation table span/budget')
    local values={};for i=0,256 do
     local v=space:read_u32(start+i);values[#values+1]=v
     if (v&0x80000000)~=0 then break end
    end
    assert((values[#values]&0x80000000)~=0,'animation table sentinel')
    table_count=table_count+1;tables[start]=true
    emit({kind=0,start=start,header=space:read_u32(start-1),values=values})
   end
   pending={kind=1,frame=frame,time=emu.time(),node=node,owner=owner,start=start,header=header,
    before_remaining=d,before_cursor=read(node+2),before_model=read(owner+17),
    after_cursor=read(node+2),after_model=read(owner+17)}
  end))
  taps[#taps+1]=space:install_write_tap(0x1000,0x3ffff,'animation_result',guarded(function(o,d,m)
   trace(1,o,d)
   local pc=cpu.state.PC.value
   if pc==0xe8ce then
    assert(pending and o==pending.node+3,'animation countdown owner');pending.after_remaining=d
    if (d&0x80000000)==0 and d>0 then finish() end
   elseif pc==0xe8d2 then
    assert(pending and o==pending.node+3,'animation period owner');pending.after_remaining=d
   elseif pc==0xe8d9 then
    assert(pending and o==pending.node+2,'animation cursor owner');pending.after_cursor=d
   elseif pc==0xe8db then
    assert(pending and o==pending.owner+17,'animation model owner');pending.after_model=d;finish()
   end
  end))
 elseif n==last+1 then complete=true;close() end
end
