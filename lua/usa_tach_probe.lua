-- Bounded read-only provenance for USA v4.5's colored tachometer pixels.
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnusa','USA v4.5 only')
local first=tonumber(os.getenv('CRUISN_TACH_FIRST') or '2640')
local last=tonumber(os.getenv('CRUISN_TACH_LAST') or '2720')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first and last-first<=240)
local frame,taps,out,seen,failed=0,{},nil,{},nil
local function close()
    for _,t in ipairs(taps) do t:remove() end
    taps={}
    if out then out:close();out=nil end
end
cruisn_tach_stop=emu.add_machine_stop_notifier(close)
return function(n)
    if failed then error(failed) end
    frame=n
    if n==first then
        assert(s:read_u32(0xa7c2)==0x1541c200 and s:read_u32(0x7a91)==0x0848c200,'USA formatter signature')
        local program=assert(io.open('tach-program.bin','wb'))
        for a=0,0x1ffff do program:write(string.pack('<I4',s:read_u32(a))) end
        program:close()
        out=assert(io.open('tach-writers.csv','w'))
        out:write('frame,kind,pc,address,data,sp,ar0,ar1,ar2,ar3,ar4,ar5,r0,r1,r2,r3,r4,r5,stack0,stack1,stack2,stack3\n')
        local function tap(kind,lo,hi)
            table.insert(taps,s:install_write_tap(lo,hi,'tach_'..kind,function(o,d,m)
                local ok,err=pcall(function()
                local pc=cpu.state.PC.value
                local key=tostring(frame)..':'..kind..':'..tostring(pc)
                if seen[key] then return end
                seen[key]=true
                out:write(string.format('%d,%s,%x,%x,%x',frame,kind,pc,o,d))
                for _,name in ipairs({'SP','AR0','AR1','AR2','AR3','AR4','AR5','R0','R1','R2','R3','R4','R5'}) do
                    out:write(string.format(',%x',cpu.state[name].value))
                end
                local sp=cpu.state.SP.value
                assert((sp>=4 and sp<0x20000) or (sp>=0x809804 and sp<0x80a000),'Unexpected stack')
                for i=0,3 do out:write(string.format(',%x',s:read_u32(sp-i))) end
                out:write('\n')
                end)
                if not ok then failed=err end
            end))
        end
        tap('texture',0xb78c80,0xb7c4ff)
        tap('palette',0x9e5500,0x9e55ff)
    elseif n==last+1 then close() end
end
