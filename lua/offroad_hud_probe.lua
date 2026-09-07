-- Read-only, bounded provenance of Off Road's numeric HUD submissions.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='offroadc','Off Road only')
local frame,pending,taps,out,failed=0,{},{},nil,nil
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if out then out:close();out=nil end
end
cruisn_offroad_hud_stop=emu.add_machine_stop_notifier(close)
return function(n)
 if failed then error(failed) end
 frame=n
 if n==4200 then
  assert(s:read_u32(0xf298)==0x68200001 and s:read_u32(0xa5c6)==0x6200f280,'Off Road HUD code mismatch')
  out=assert(io.open('offroad-hud-writers.csv','w'))
  out:write('frame,palette,x,y,pc,sp,ar0,ar1,ar2,ar3,ar4,ar5,ar6,ar7')
  for i=0,23 do out:write(',stack'..i) end;out:write('\n')
  table.insert(taps,s:install_write_tap(0x600000,0x600000,'offroad_hud_words',function(o,d,m)
   if #pending<16 then table.insert(pending,d&0xffff) end
  end))
  table.insert(taps,s:install_read_tap(0x980083,0x980083,'offroad_hud_trigger',function(o,d,m)
   local ok,err=pcall(function()
    if #pending>=15 and (pending[2]==0x2200 or pending[2]==0x2180) then
     local sp=cpu.state.SP.value
     assert((sp>=24 and sp<0x20000) or (sp>=0x400018 and sp<0x420000) or
            (sp>=0x809800 and sp<0x80a000),string.format('Unexpected Off Road stack %x',sp))
     out:write(string.format('%d,%x,%d,%d,%x,%x',frame,pending[2],pending[3],pending[4],cpu.state.PC.value,sp))
     for _,a in ipairs({'AR0','AR1','AR2','AR3','AR4','AR5','AR6','AR7'}) do out:write(string.format(',%x',cpu.state[a].value)) end
     for i=0,23 do
      -- A shallow internal stack has fewer than 24 mapped words below SP.
      local a=sp-i
      local v=(sp>=0x809800 and a<0x809800) and 0 or s:read_u32(a)
      out:write(string.format(',%x',v))
     end
     out:write('\n')
    end
   end)
   pending={};if not ok then failed=err end
  end))
 elseif n==4203 then close() end
end
