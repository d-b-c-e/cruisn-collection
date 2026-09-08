-- Read-only USA4.5 pending/active list probe. No admissions are changed.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnusa','USA4.5 only')
local first=tonumber(os.getenv('CRUISN_RESIDENCY_FIRST') or '2500')
local last=tonumber(os.getenv('CRUISN_RESIDENCY_LAST') or '4300')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=12000,'invalid residency interval')
local far=tonumber(os.getenv('MIDV_USA_FAR') or '80000')
assert(far==80000 or far==100000 or far==160000 or far==240000,'invalid USA far')
local extended=os.getenv('MIDV_USA_FAR') and os.getenv('MIDV_USA_RESIDENCY')~='0'
local admission=extended and far*15//16 or 75000
local removal=extended and far or 80000
local frame,tap,out,failed,checks=0,nil,nil,nil,0
local function signed(v) return v>=0x80000000 and v-0x100000000 or v end
local function close()
 if tap then tap:remove();tap=nil end
 if out then out:close();out=nil end
end
cruisn_usa_residency_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failed,failed)
 if n==first then
  for _,w in ipairs({{0x729b,0x0824727d},{0x72af,0x1541011c},{0x72b1,0x18010004},
      {0x72b2,0x1841011d},{0x72b7,0x1ae03000},{0x72b8,0x1540010e},
      {0x7280,0x0824727e},{0x728e,0x1ae03000},{0x728f,0x1540010e},
      {0x727d,75000},{0x727e,80000}}) do
   assert(s:read_u32(w[1])==w[2],string.format('USA residency signature mismatch at %x',w[1]))
  end
  out=assert(io.open('usa-residency.csv','w'));out:setvbuf('full',65536)
  out:write('frame,kind,object,model,flags,depth,radius,limit\n')
  tap=s:install_write_tap(0x1000,0x1ffff,'usa_residency_observer',function(o,d,m)
   if failed then return end
   local ok,reason=pcall(function()
    local pc=cpu.state.PC.value
    local kind=pc==0x72b0 and 'pending' or pc==0x72b9 and 'activate' or pc==0x7290 and 'deactivate'
    if not kind then return end
    local object=cpu.state.AR1.value
    assert(object>=0x1000 and object+29<0x20000,'USA list object outside backing RAM')
    assert(o==object+(kind=='pending' and 28 or 14),'USA list write offset changed')
    local depth=kind=='pending' and signed(d) or signed(s:read_u32(object+28))
    local flags=kind=='pending' and s:read_u32(object+14) or d
    local limit=cpu.state.R4.value
    assert(limit==(kind=='deactivate' and removal or admission),'USA active limit changed')
    out:write(string.format('%d,%s,%x,%x,%x,%d,%d,%d\n',frame,kind,object,
        s:read_u32(object+13),flags,depth,signed(s:read_u32(object+29)),limit))
    if kind=='pending' then checks=checks+1 end
   end)
   if not ok then failed=tostring(reason) end
   -- No replacement data is returned to MAME.
  end)
 elseif n==last+1 then close();assert(checks>0,'no pending checks observed') end
end
