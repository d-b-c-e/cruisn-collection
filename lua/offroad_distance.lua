-- Off Road 1.63 culler/table/camera/ADC profile, read-only by default.
-- CRUISN_OFFROAD_MULTIPLIER=1/2/3 opts into a bounded MUTATING diagnostic:
-- active far/clip limits, their initializers and the table ceiling change only
-- during this interval. The game reinitializes these at the race transition.
-- The virtual reciprocal tail never overwrites underlying ROM/resource bytes.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='offroadc','Off Road1.63 only')
local first=tonumber(os.getenv('CRUISN_OFFROAD_FIRST') or '1800')
local last=tonumber(os.getenv('CRUISN_OFFROAD_LAST') or '5990')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>first and last-first<=12000)
local multiplier=tonumber(os.getenv('CRUISN_OFFROAD_MULTIPLIER') or '0')
assert(multiplier==0 or multiplier==1 or multiplier==2 or multiplier==3,'unsupported Off Road multiplier')
local frame,taps,out,tableout,camera,adc,failed,limit=0,{},nil,nil,nil,nil,nil,nil
local writes=nil
local restored,maximum={},63679
local far_tests,stock_rejects,rejects,extra=0,0,0,0
local consumers={}
local base=0xcb0fc8
local function regfloat(name)
 return string.unpack('<f',string.pack('<I4',cpu.state[name].value&0xffffffff))
end
local function flush()
 if not out then return end
 assert(out:write(string.format('%d,%d,%d,%d,%d,%d\n',frame,limit,far_tests,stock_rejects,rejects,extra)))
 local pcs={};for pc in pairs(consumers) do pcs[#pcs+1]=pc end;table.sort(pcs)
 for _,pc in ipairs(pcs) do
  local v=consumers[pc]
  assert(tableout:write(string.format('%d,%x,%08x,%d,%d,%d,%d\n',frame,pc,s:read_u32(pc-1),v.n,v.lo,v.hi,v.clamped)))
 end
 far_tests,stock_rejects,rejects,extra=0,0,0,0;consumers={}
end
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 for _,w in ipairs(restored) do
  assert(s:read_u32(w[1])==w[3],'trial word changed before restore')
  s:write_u32(w[1],w[2])
 end
 restored={}
 for _,f in ipairs({out,tableout,camera,adc,writes}) do if f then f:close() end end
 writes=nil
 out,tableout,camera,adc=nil,nil,nil,nil
end
cruisn_offroad_distance_stop=emu.add_machine_stop_notifier(close)
local function tap(a,b,name,callback)
 taps[#taps+1]=s:install_read_tap(a,b,name,function(o,d,m)
  if failed then return end
  local ok,reason=pcall(callback,o,d,m);if not ok then failed=tostring(reason) end
  -- No replacement return value: the explicit checked patch owns any trial.
 end)
end
local function c31(value)
 local ieee=string.unpack('<I4',string.pack('<f',value))
 return ((((ieee>>23)-127)&255)<<24)|(ieee&0x7fffff)
end
local function begin_trial()
 if multiplier==0 then return end
 local sites={
  {0x1c44,0x0a414000},{0x1c46,0x0a404000},{0x1c4e,0x0a424000},
  {0x1d1c,0x24e14005},{0x1d1f,0x24e14005},{0x1d23,0x24e14005},
  {0x1d26,0x24e14085},{0x1d2a,0x24e14005},{0x1d2d,0x24e14005},
  {0x1d31,0x24e14085},{0x1d34,0x24e14005},{0x1d38,0x24e14005},
  {0x1daf,0x24e1400b},{0x1db0,0x800f40c3},{0x1dc4,0x07474000},
  {0x1e2e,0x24e1400b},{0x1e2f,0x800f40c3},{0x1e50,0x24e1400b},{0x1e51,0x800f40c3},
  {0x1e90,0x24e1400b},{0x1e91,0x800f40c3},{0x1ed1,0x24e1400b},{0x1ed2,0x800f40c3},
  {0x1f11,0x24e1400b},{0x1f12,0x800f40c3},{0x1f52,0x24e1400b},{0x1f53,0x800f40c3},
  {0x22e2,0x24e14002},{0x22e5,0x24e14002},{0x22e9,0x24e14002},{0x22ec,0x24e14002},
  {0x230f,0x24e1400b},{0x2310,0x800f40c3},{0x2342,0x24e14002},{0x2345,0x24e14002},
  {0x2349,0x24e14002},{0x234c,0x24e14002},{0x236f,0x24e1400b},{0x2370,0x800f40c3},
  {0x239c,0x07404000},{0x2562,0x24e14002},{0x2565,0x24e14002},
  {0x2569,0x24e14002},{0x256c,0x24e14002},{0x257e,0x0a414000},{0x2580,0x0a404000},
  {0x2588,0x0a424000},{0x25cf,0x24e1400b},{0x25d0,0x800f40c3},
  {0x27ae,0x24e1400b},{0x27af,0x800f40c3},{0x2822,0x24e14002},{0x2825,0x24e14002},
  {0x2829,0x24e14002},{0x282c,0x24e14002},{0x284f,0x24e1400b},{0x2850,0x800f40c3},
  {0xe035,0x07404000},{0xe221,0x07424000}}
 local pcs={}
 for _,w in ipairs(sites) do
  assert(s:read_u32(w[1])==w[2],string.format('projection instruction mismatch at%x',w[1]))
  pcs[w[1]+1]=true
 end
 maximum=63680*multiplier-1
 local words={{0x1b724,0x0f38c000,c31(47296*multiplier)},
              {0x1b725,0x0f78c000,c31(63680*multiplier)},
              {0x11221,0x0f38c000,c31(47296*multiplier)},
              {0x11223,0x0f78c000,c31(63680*multiplier)},
              {0x111a8,63679,maximum}}
 for _,w in ipairs(words) do assert(s:read_u32(w[1])==w[2],'trial requires original active limits') end
 if multiplier>1 then
  local cache={}
  for i=63680,maximum do
   -- Exact rational, eight decimals, ties-to-even. Binary floating round()
   -- disagreed with two existing table entries; preserve integer arithmetic.
   local denominator=i+1;local numerator=50400000000
   local q=numerator//denominator;local r=numerator%denominator
   if r*2>denominator or (r*2==denominator and q%2==1) then q=q+1 end
   cache[i]=c31(q/100000000)
  end
  taps[#taps+1]=s:install_read_tap(base+63680,0xffffff,'offroad_virtual_tail',function(o,d,m)
   if failed or cpu.state.AR0.value~=base or o~=base+cpu.state.IR0.value then return end
   local ok,result=pcall(function()
    assert(pcs[cpu.state.PC.value],string.format('unattributed extended projection pc=%x offset=%x IR0=%x',cpu.state.PC.value,o,cpu.state.IR0.value))
    assert(cache[o-base],'extended projection exceeded coherent limit')
    return cache[o-base]
   end)
   if not ok then failed=tostring(result);return end
   return result
  end)
 end
 for _,w in ipairs(words) do s:write_u32(w[1],w[3]);restored[#restored+1]=w end
end
return function(n)
 assert(not failed,failed)
 if out then flush() end
 frame=n
 if n==first then
  begin_trial()
  for _,w in ipairs({{0x1c35,0x0420b724},{0x1c36,0x6a2a066c},{0x1c42,0x04b111a8},
      {0x1c43,0x54b111a8},{0x1c44,0x0a414000},{0x111a7,base},{0x111a8,maximum},
      {0x1820,0x07201221},{0x1821,0x1420b724},{0x11223,c31(63680*math.max(1,multiplier))},
      {0x1822,0x07201223},{0x1823,0x1420b725},
      {0x1b725,c31(63680*math.max(1,multiplier))},{0x1bfc,0x082f120b},{0x1120b,0x196f3}}) do
   assert(s:read_u32(w[1])==w[2],string.format('Off Road profile mismatch at%x',w[1]))
  end
  local word=s:read_u32(0x11221)
  assert(word==0x0f38c000 or word==0x0f66f000 or (multiplier>0 and word==c31(47296*multiplier)),
         'unsupported Off Road far trial')
  limit=multiplier>0 and 47296*multiplier or (word==0x0f38c000 and 47296 or 59120)
  word=c31(limit)
  assert(s:read_u32(0x1b724)==word,'Off Road requested far did not reach active culler')
  out=assert(io.open('offroad-distance.csv','w'));out:setvbuf('full',65536)
  out:write('frame,far,far_tests,stock_rejects,far_rejects,extra_admissions\n')
  tableout=assert(io.open('offroad-projection.csv','w'));tableout:setvbuf('full',65536)
  tableout:write('frame,pc,opcode,reads,minimum_index,maximum_index,upper_clamps\n')
  camera=assert(io.open('offroad-camera.csv','w'));camera:setvbuf('full',65536)
  camera:write('frame,x,y,z,m0,m1,m2,m3,m4,m5,m6,m7,m8\n')
  adc=assert(io.open('offroad-adc.csv','w'));adc:setvbuf('full',65536)
  adc:write('frame,time,pc,value\n')
  writes=assert(io.open('offroad-limit-writes.csv','w'));writes:setvbuf('full',65536)
  writes:write('frame,pc,address,value\n')
  taps[#taps+1]=s:install_write_tap(0x1b724,0x1b725,'offroad_limit_producer',function(o,d)
   local ok,reason=pcall(function()
    assert(writes:write(string.format('%d,%x,%x,%08x\n',frame,cpu.state.PC.value,o,d)))
   end)
   if not ok then failed=tostring(reason) end
  end)
  tap(0x1b724,0x1b724,'offroad_far',function(o,d)
   if cpu.state.PC.value~=0x1c36 then return end
   assert(d==word,'Off Road far changed during observation')
   local depth=regfloat('R0F')
   assert(depth==depth and math.abs(depth)<math.huge,'invalid culler depth')
   far_tests=far_tests+1
   if depth>=47296 then stock_rejects=stock_rejects+1 end
   if depth>=limit then rejects=rejects+1 elseif depth>=47296 then extra=extra+1 end
  end)
  tap(base-4096,base+maximum,'offroad_all_projection',function(o,d)
   if cpu.state.AR0.value~=base then return end
   local index=cpu.state.IR0.value;if index>=0x80000000 then index=index-0x100000000 end
   if o~=base+index then return end
   local pc=cpu.state.PC.value;assert(pc>0 and pc<0x20000,'unexpected table caller')
   local i=o-base;local v=consumers[pc] or {n=0,lo=i,hi=i,clamped=0};consumers[pc]=v
   v.n=v.n+1;v.lo=math.min(v.lo,i);v.hi=math.max(v.hi,i)
   if i==maximum then v.clamped=v.clamped+1 end
  end)
  tap(0x993000,0x993000,'offroad_actual_adc',function(o,d)
   assert(adc:write(string.format('%d,%.12f,%x,%x\n',frame,emu.time(),cpu.state.PC.value,d)))
  end)
 end
 if camera and n<=last then
  assert(s:read_u32(0x1120b)==0x196f3,'camera matrix pointer changed')
  assert(camera:write(n))
  for _,i in ipairs({3,7,11,0,1,2,4,5,6,8,9,10}) do assert(camera:write(string.format(',%08x',s:read_u32(0x196f3+i)))) end
  assert(camera:write('\n'))
 end
 if n==last+1 then close() end
end
