-- Read-only World 2.4 investigation of a scenery object becoming available.
-- The event trace first submits modelCCF288 in slot12668 at3019, already inside
-- the original far range. Trace the model-slot writer, not just its later cull.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 activation diagnostic only')
local first=tonumber(os.getenv('CRUISN_ACTIVATION_FIRST') or '5990')
local last=tonumber(os.getenv('CRUISN_ACTIVATION_LAST') or '6230')
local object=tonumber(os.getenv('CRUISN_ACTIVATION_OBJECT') or '11c04',16)
local model=tonumber(os.getenv('CRUISN_ACTIVATION_MODEL') or 'cb2315',16)
local assignments_only=os.getenv('CRUISN_ACTIVATION_ASSIGNMENTS_ONLY')=='1'
-- Explicitly watch an already allocated object; never silently accept a missed
-- assignment in the default allocation investigation.
local watch_existing=true
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=(assignments_only and 9000 or 240)
    and object and object>=0x10000 and object<0x1ff00
    and model and model>=0xc00000 and model<=0xffffff
    and not (watch_existing and assignments_only),'invalid activation target')
local frame,tap,out,frames=0,nil,nil,nil
local captured,writes=false,0
local function capture_program()
    local f=assert(io.open('scenery-activation-program.bin','wb'))
    local chunk={}
    for a=0,0x1ffff do
        chunk[#chunk+1]=string.pack('<I4',s:read_u32(a))
        if #chunk==1024 then f:write(table.concat(chunk));chunk={} end
    end
    f:close();captured=true
end
local function close()
    if tap then tap:remove();tap=nil end
    if out then out:close();out=nil end
    if frames then frames:close();frames=nil end
end
cruisn_scenery_activation_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==first then
        assert(s:read_u32(0x9c)>>16==0x1529,'World object signature mismatch')
        if watch_existing then
            assert(s:read_u32(object+13)==model,'existing target model does not match')
            capture_program()
        end
        local metadata=assert(io.open('scenery-activation-mode.csv','w'))
        metadata:write('mode,object,model,first,last\n')
        metadata:write(string.format('%s,%x,%x,%d,%d\n',
            watch_existing and 'watch_existing' or 'require_assignment',object,model,first,last))
        metadata:close()
        out=assert(io.open('scenery-activation.csv','w'))
        if not assignments_only then
            frames=assert(io.open('scenery-activation-frames.csv','w'))
            frames:write('frame')
            for i=0,27 do frames:write(string.format(',word_%02x',i)) end
            frames:write('\n')
        end
        out:write('frame,word_address,pc,value,r0,r1,r2,r3,ar0,ar1,ar2,ar3,ar4,ar5,ar6,ar7,sp,stack0,stack1,stack2,stack3\n')
        tap=s:install_write_tap(assignments_only and object+13 or object,
            assignments_only and object+13 or object+27,'scenery_object_assignment',function(o,d,m)
            if watch_existing and o==object+13 and d~=model then
                error('existing target slot was reassigned during observation')
            end
            writes=writes+1
            out:write(string.format('%d,%x,%x,%x',frame,o,cpu.state.PC.value,d))
            for _,name in ipairs({'R0','R1','R2','R3','AR0','AR1','AR2','AR3','AR4','AR5','AR6','AR7','SP'}) do
                out:write(string.format(',%x',cpu.state[name].value))
            end
            local sp=cpu.state.SP.value
            for i=0,3 do
                local a=sp-i
                -- World uses the CPU's mapped internal RAM for its call stack.
                -- Empty cells mean outside known RAM, never a fabricated zero.
                local ram=(a>=0 and a<0x20000) or (a>=0x809800 and a<=0x809fff)
                out:write(ram and string.format(',%x',s:read_u32(a)) or ',')
            end
            out:write('\n')
            if o==object+13 and d==model and not captured then
                -- Program RAM only, no I/O reads. At the write callback, before
                -- relying on a later snapshot after the factory has returned.
                capture_program()
            end
        end)
    elseif n==last+1 then
        close()
        assert(captured,'target model assignment not observed')
        assert(not watch_existing or writes>0,'existing target had no observed writes')
    end
    if frames then
        frames:write(tostring(n))
        for i=0,27 do frames:write(string.format(',%x',s:read_u32(object+i))) end
        frames:write('\n')
    end
end
