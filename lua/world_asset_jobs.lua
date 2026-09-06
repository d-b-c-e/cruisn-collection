-- Read-only World 2.4 texture-job provenance around transmission selection.
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World2.4 diagnostic only')
local first=tonumber(os.getenv('CRUISN_ASSET_FIRST') or '1100')
local last=tonumber(os.getenv('CRUISN_ASSET_LAST') or '1400')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first and last-first<=1800)
local frame,taps,out=0,{},nil
local function close()
    for _,t in ipairs(taps) do t:remove() end
    taps={}
    if out then out:close();out=nil end
end
cruisn_asset_jobs_stop=emu.add_machine_stop_notifier(close)
local function log(kind,offset,data)
    out:write(string.format('%d,%s,%x,%x,%x',frame,kind,cpu.state.PC.value,offset,data))
    for _,name in ipairs({'SP','AR0','AR1','AR2','AR3','AR4','AR5','R0','R1','R2'}) do
        out:write(string.format(',%x',cpu.state[name].value))
    end
    local sp=cpu.state.SP.value
    for i=0,11 do out:write(string.format(',%x',s:read_u32(sp-i))) end
    out:write('\n')
end
return function(n)
    frame=n
    if n==first then
        assert(s:read_u32(0xb4d)==0x0820eb43 and s:read_u32(0xb52)==0x0828b5a0,'loader signature')
        out=assert(io.open('asset-jobs.csv','w'))
        out:write('frame,kind,pc,address,data,sp,ar0,ar1,ar2,ar3,ar4,ar5,r0,r1,r2')
        for i=0,11 do out:write(',stack'..i) end
        out:write('\n')
        table.insert(taps,s:install_read_tap(0xb5a0,0xb5a0,'asset_job_head',function(o,d,m)
            if cpu.state.PC.value==0xb53 then log('dequeue',o,d) end
        end))
        table.insert(taps,s:install_write_tap(0xeb43,0xeb46,'asset_job_state',function(o,d,m)
            log('state',o,d)
        end))
        table.insert(taps,s:install_write_tap(0xbcc100,0xbcc100,'asset_job_atlas',function(o,d,m)
            log('atlas',o,d)
        end))
    elseif n==last+1 then close() end
end
