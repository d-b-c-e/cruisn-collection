-- Read-only, bounded distance diagnostics for the five supported ROM revisions.
-- All addresses are word addresses. No table tap reads guest memory recursively.
-- Use replay.py --probe-script; failures from taps are propagated to session.lua.
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces.program
local game=manager.machine.system.name
local first=tonumber(os.getenv('CRUISN_DISTANCE_FIRST') or '2500')
local last=tonumber(os.getenv('CRUISN_DISTANCE_LAST') or '4300')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=12000,'invalid distance trace interval')
local profiles={
 crusnusa={far=0x55,pc=0xcc,object='AR0',flags=14,depth='R3',radius='R4',
  base=0xb2b3,tablepc=0xd6,index='AR3',absolute=true,
  globals={0x52,0x55,0x727d,0x727e},
  guards={{0xcb,0x04a30055},{0xd0,0x04e31387},{0xd1,0x54e31387},
   {0xd5,0x0741c300},{0x52,0xb2b3},{0x727d,75000},{0x727e,80000},
   {0x729b,0x0824727d},{0x72b1,0x18010004},{0x72b2,0x1841011d}}},
 crusnwld24={far=0x40,pc=0xa1,object='AR0',flags=14,depth='R3',radius='R4',
  base=0xb66f,tablepc=0xb4,index='AR3',absolute=true,
  globals={0x40,0x4d,0xd58c},
  guards={{0xa0,0x04a30040},{0xae,0x04e31387},{0xaf,0x54e31387},
   {0xb3,0x0741c300},{0x4d,0xb66f},{0x7b50,0x0224d58c},{0x7b5c,0x1ae03000}}},
 crusnwld={far=0x40,pc=0xa1,object='AR0',flags=14,depth='R3',radius='R4',
  base=0xb665,tablepc=0xb4,index='AR3',absolute=true,
  globals={0x40,0x4d,0xd586},
  guards={{0xa0,0x04a30040},{0xae,0x04e31387},{0xaf,0x54e31387},
   {0xb3,0x0741c300},{0x4d,0xb665},{0x7b42,0x0224d586},{0x7b4e,0x1ae03000}}},
 offroadc={far=0x1b724,pc=0x1c36,object='AR6',flags=5,depth='R0F',radius='R1F',
  float=true,base=0xcb0fc8,tablepc=0x1c45,index='IR0',tablemax=63679,
  globals={0x111a7,0x111a8,0x11221,0x11223,0x1b724,0x1b725},
  guards={{0x1c34,0x26800201},{0x1c35,0x0420b724},{0x1c42,0x04b111a8},
   {0x1c43,0x54b111a8},{0x1c44,0x0a414000},{0x111a7,0xcb0fc8},
   {0x111a8,63679},{0x1820,0x07201221},{0x1821,0x1420b724}}},
 crusnexo={far=0x67da,pc=0x6888,object='AR7',flags=15,depth='R2',radius_offset=21,
  base=0xeaab,tablepc=0x688c,index='IR0',plus_radius=true,
  globals={0x67cc,0x67da},
  guards={{0x67cc,0xeaab},{0x6882,0x02420715},{0x6885,0x04e31387},
   {0x6886,0x54e31387},{0x6887,0x04a267da},{0x688b,0x07404300}}}
}
local p=assert(profiles[game],'unsupported distance profile')
local frame,taps,out,meta,failed,far_reads,table_reads=0,{},nil,nil,nil,0,0
local function signed(v) return v>=0x80000000 and v-0x100000000 or v end
local function c31(v)
 if v==0x80000000 then return 0 end
 local e=v>>24;if e>=128 then e=e-256 end
 return ((v&0x7fffff)/8388608+((v&0x800000)==0 and 1 or -2))*2^e
end
local function reg(name)
 local v=cpu.state[name].value
 if name:sub(-1)=='F' then return string.unpack('<f',string.pack('<I4',v&0xffffffff)) end
 return signed(v)
end
local function close()
 for _,tap in ipairs(taps) do tap:remove() end;taps={}
 if out then out:close();out=nil end
 if meta then meta:close();meta=nil end
end
local function tap(a,b,name,callback)
 taps[#taps+1]=s:install_read_tap(a,b,name,function(o,d,m)
  if failed then return end
  local ok,reason=pcall(callback,o,d,m)
  if not ok then failed=tostring(reason) end
  -- Deliberately no replacement return value: this is read-only.
 end)
end
cruisn_distance_capability_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n
 assert(not failed,failed)
 if n==first then
  for _,w in ipairs(p.guards) do
   assert(s:read_u32(w[1])==w[2],string.format('distance profile mismatch at %x',w[1]))
  end
  meta=assert(io.open('distance-layout.csv','w'));meta:write('rom,kind,address,value\n')
  for _,w in ipairs(p.guards) do meta:write(string.format('%s,guard,%x,%x\n',game,w[1],w[2])) end
  for _,a in ipairs(p.globals) do meta:write(string.format('%s,global,%x,%x\n',game,a,s:read_u32(a))) end
  for _,i in ipairs({100,1000,4900,4999,p.tablemax or 4999}) do
   meta:write(string.format('%s,table,%x,%x\n',game,p.base+i,s:read_u32(p.base+i)))
  end
  meta:flush()
  out=assert(io.open('distance-capability.csv','w'));out:setvbuf('full',65536)
  out:write('frame,kind,pc,object,flags,depth_minus_radius,radius,limit,index,raw\n')
  tap(p.far,p.far,'distance_far_observer',function(o,d)
   if cpu.state.PC.value~=p.pc then return end
   local object=cpu.state[p.object].value
   assert(object>=0x1000 and object+(p.radius_offset or p.flags)<(game=='crusnexo' and 0x40000 or 0x20000),
       'distance object outside backing RAM')
   local radius=p.radius_offset and signed(s:read_u32(object+p.radius_offset)) or reg(p.radius)
   local depth=reg(p.depth)
   if p.plus_radius then depth=depth-2*radius end
   local limit=p.float and c31(d) or d
   -- Exotica's comparison is depth+radius; retain that exact test in raw and
   -- report depth-radius separately for comparisons with the V-Unit families.
   out:write(string.format('%d,far,%x,%x,%x,%.9g,%.9g,%.9g,0,%x\n',
       frame,p.pc,object,s:read_u32(object+p.flags),depth,radius,limit,d))
   far_reads=far_reads+1
  end)
  -- Only observe each culler's one reciprocal read. The entire table range is
  -- needed to distinguish a working clamp from a gate that never reaches it.
  tap(p.base-(p.float and 4096 or 0),p.base+(p.tablemax or 4999),'distance_table_observer',function(o,d)
   if cpu.state.PC.value~=p.tablepc then return end
   local i=reg(p.index);if p.absolute then i=i-p.base end
   out:write(string.format('%d,table,%x,%x,0,0,0,0,%d,%x\n',
       frame,p.tablepc,cpu.state[p.object].value,i,d))
   table_reads=table_reads+1
  end)
 elseif n==last+1 then
  close()
  assert(far_reads>0 and table_reads>0,'distance probe did not observe both renderer gates')
 end
end
