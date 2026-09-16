-- SPDX-License-Identifier: BSD-3-Clause
-- Explicit emulator actions are separate from recorded MAME input ports.
assert(os.getenv('MIDV_FFB')=='0','session actions require physical FFB0')
local plan=assert(io.open(assert(os.getenv('SNAP_ACTIONS')),'r'))
assert(plan:read('*l')=='frame,action','session action columns')
local rows={};local previous=-1;local stop=assert(tonumber(os.getenv('SNAP_STOP')))
for line in plan:lines() do
 local text=line:match('^(%d+),soft_reset$');local frame=tonumber(text)
 assert(frame and frame%1==0 and frame>=1 and frame<=stop-2 and frame>=previous+2 and #rows<16,'session action bounds/order')
 rows[#rows+1]=frame;previous=frame
end
assert(plan:close());assert(#rows>0,'empty session actions')
local out=assert(io.open(assert(os.getenv('SNAP_ACTION_LOG')),'w'))
assert(out:write('id,event,frame,time\n'))
local state={frame=0,next=1,pending=false,failed=nil}
local function emit(event)
 assert(out:write(string.format('%d,%s,%d,%.12f\n',state.next,event,state.frame,emu.time())))
 assert(out:flush())
end
state.reset=emu.add_machine_reset_notifier(function()
 local ok,reason=pcall(function()
  assert(state.pending,'unrequested emulator reset')
  emit('complete');state.pending=false;state.next=state.next+1
 end)
 if not ok then state.failed=tostring(reason) end
end)
return {
 tick=function(frame)
  assert(not state.failed,state.failed);state.frame=frame
  if state.pending then assert(frame<=rows[state.next]+1,'session reset did not complete') end
  if rows[state.next]==frame then
   assert(not state.pending,'overlapping session resets');state.pending=true
   emit('request');manager.machine:soft_reset()
  end
 end,
 close=function()
  local ok,reason=out:close()
  assert(ok,reason);assert(not state.failed,state.failed)
  assert(not state.pending and state.next==#rows+1,'incomplete session reset schedule')
 end
}
