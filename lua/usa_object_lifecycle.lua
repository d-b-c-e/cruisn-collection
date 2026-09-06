-- Bounded read-only USA v4.5 object/LOD probe. Use replay.py --probe-script.
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces.program
local first=tonumber(os.getenv('CRUISN_OBJECT_FIRST') or '2900')
local last=tonumber(os.getenv('CRUISN_OBJECT_LAST') or '3800')
assert(manager.machine.system.name=='crusnusa','object probe supports USA v4.5 only')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first and last-first<=3600,'invalid bounded object trace interval')
local verified=false
local frame=0
local out=assert(io.open('lifecycle.csv','w'))
out:write('frame,object,model,flags,depth_minus_radius,radius,far_limit,x,y,z,base_model,mid_model,far_model\n')
local tap=s:install_read_tap(0x55,0x55,'object_far_gate',function(offset,data,mask)
 if not verified or frame<first or frame>last or cpu.state.PC.value~=0xcc then return end
 local id=cpu.state.AR0.value
 local function signed(n) return n>=0x80000000 and n-0x100000000 or n end
 out:write(string.format('%d,%x,%x,%x,%d,%d,%d,%x,%x,%x,%x,%x,%x\n',frame,id,cpu.state.AR1.value-1,s:read_u32(id+14),signed(cpu.state.R3.value),signed(cpu.state.R4.value),data,s:read_u32(id+1),s:read_u32(id+2),s:read_u32(id+3),s:read_u32(id+13),s:read_u32(id+24),s:read_u32(id+25)))
end)
cruisn_lifecycle_stop=emu.add_machine_stop_notifier(function() tap:remove();out:close() end)
return function(n)
 frame=n
 if n==first then
  assert(s:read_u32(0xcb)==0x04a30055 and s:read_u32(0xbf)==0x04e21f40,
   'USA object culler signature mismatch; no trace is valid')
  verified=true
 end
end
