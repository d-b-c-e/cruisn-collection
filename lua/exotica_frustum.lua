-- Read-only Exotica 2.4 CPU sphere-culler audit. No guest writes or replacement reads.
-- Cache object/fast RAM at the far comparison, never from a reciprocal-table tap.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnexo','Exotica2.4 only')
local first=tonumber(os.getenv('CRUISN_EXOTICA_FIRST') or '2500')
local last=tonumber(os.getenv('CRUISN_EXOTICA_LAST') or '4300')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>first and last-first<=12000)
local frame,taps,out,current,failed,sequence,list=0,{},nil,nil,nil,0,0
local function signed(v) return v>=0x80000000 and v-0x100000000 or v end
local function flush()
 if not current then return end
 local r=current
 assert(out:write(string.format('%d,%d,%x,%x,%x,%x,%d,%d,%d,%d,%08x,%08x,%08x,%08x,%s,%s,%s,%s,%d\n',
  r.frame,r.seq,r.list,r.object,r.flags,r.model,r.depth,r.radius,r.index,r.far,
  r.x,r.y,r.z,r.factor,r.yl or '',r.yu or '',r.xl or '',r.xu or '',r.accepted)))
 current=nil
end
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if out then flush();out:close();out=nil end
end
cruisn_exotica_frustum_stop=emu.add_machine_stop_notifier(close)
local function tap(a,b,name,callback)
 taps[#taps+1]=s:install_read_tap(a,b,name,function(o,d)
  if failed then return end
  local ok,reason=pcall(callback,o,d);if not ok then failed=tostring(reason) end
  -- Deliberately no replacement return value.
 end)
end
local function operand(pc,name,register)
 if cpu.state.PC.value~=pc or not current then return end
 assert(cpu.state.AR7.value==current.object,'culler object changed inside sphere tests')
 assert(not current[name],'duplicate sphere operand')
 current[name]=string.format('%08x',cpu.state[register].value&0xffffffff)
end
return function(n)
 frame=n;assert(not failed,failed)
 if n==first then
  for _,w in ipairs({{0x67c3,0x87ff48},{0x67cc,0xeaab},{0x67da,204800},
    {0x67d1,0x07480000},{0x67d0,0x08000000},{0x67ce,0x087f8000},
    {0x6882,0x02420715},{0x6885,0x04e31387},{0x6886,0x54e31387},
    {0x6887,0x04a267da},{0x688b,0x07404300},{0x688f,0x01a267d1},
    {0x6892,0x042367d1},{0x6897,0x01a267d0},{0x689b,0x042267ce},
    {0x68a3,0x1a2667d9},{0x681f,0x082fbbb5},{0x6823,0x082fbbb6},
    {0x682f,0x082fbbb7},{0x6833,0x082fbbb8}}) do
   assert(s:read_u32(w[1])==w[2],string.format('Exotica frustum profile mismatch at%x',w[1]))
  end
  out=assert(io.open('exotica-frustum.csv','w'));out:setvbuf('full',65536)
  out:write('frame,sequence,list,object,flags,model,depth,radius,index,far,x,y,z,factor,yl,yu,xl,xu,accepted\n')
  tap(0xbbb5,0xbbb8,'exotica_render_lists',function(o,d)
   local pcs={[0x6820]=0xbbb5,[0x6824]=0xbbb6,[0x6830]=0xbbb7,[0x6834]=0xbbb8}
   if pcs[cpu.state.PC.value]==o then list=o end
  end)
  tap(0x67da,0x67da,'exotica_far_and_pose',function(o,d)
   if cpu.state.PC.value~=0x6888 then return end
   flush()
   if frame>last then return end
   local object=cpu.state.AR7.value
   assert(object>=0x1000 and object+0x16<0x40000,'object outside backing RAM')
   -- These reads cannot recursively hit this tap, even for a corrupt object.
   assert(object+0x14~=0x67da and object+0x15~=0x67da and object+0xf~=0x67da and object+0x11~=0x67da)
   local depth=signed(s:read_u32(object+0x14));local radius=signed(s:read_u32(object+0x15))
   local index=cpu.state.R3.value
   assert(d==204800 and signed(cpu.state.R2.value)==depth+radius,'far comparison changed')
   assert(index==math.min(4999,math.max(0,depth)//16),'culler clamp does not match cached depth')
   assert(cpu.state.AR3.value==0xeaab and cpu.state.AR6.value==0x87ff48,'culler bases changed')
   sequence=sequence+1
   current={frame=frame,seq=sequence,list=list,object=object,flags=s:read_u32(object+0xf),
    model=s:read_u32(object+0x11),depth=depth,radius=radius,index=index,far=d,
    x=s:read_u32(0x87ff47),y=s:read_u32(0x87ff48),z=s:read_u32(0x87ff49),
    factor=s:read_u32(0xeaab+index),accepted=0}
  end)
  tap(0x67d1,0x67d1,'exotica_y_planes',function(o,d)
   operand(0x6890,'yl','R2F');operand(0x6893,'yu','R3F')
  end)
  tap(0x67d0,0x67d0,'exotica_x_lower',function(o,d) operand(0x6898,'xl','R2F') end)
  tap(0x67ce,0x67ce,'exotica_x_upper',function(o,d) operand(0x689c,'xu','R2F') end)
  -- The 0FF9 read at689D is inside the final X-reject branch delay slots.
  -- 68A3 executes after those slots and therefore proves all sphere tests passed.
  tap(0x67d9,0x67d9,'exotica_sphere_pass',function(o,d)
   if cpu.state.PC.value==0x68a4 and current then
    assert(cpu.state.AR7.value==current.object and current.xu,'sphere pass lacks matching operands')
    current.accepted=1
   end
  end)
 elseif n==last+2 then
  -- One drain frame lets the final object complete; no new rows after last.
  close();assert(sequence>0,'no Exotica culler observations')
 end
end
