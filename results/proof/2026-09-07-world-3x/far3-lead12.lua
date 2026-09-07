local callbacks={
(function()
-- Read-only, bounded World camera and actual ADC-read timeline. Camera state is
-- a route-divergence detector, not a claim that these words are vehicle physics.
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24' or manager.machine.system.name=='crusnwld')
local first=tonumber(5880)
local last=tonumber(6300)
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=12000,'invalid motion trace interval')
local frame,taps,out,adc=0,{},nil,nil
local function close()
    for _,t in ipairs(taps) do t:remove() end
    taps={}
    if out then out:close();adc:close();out=nil end
end
cruisn_world_motion_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==first then
        assert(s:read_u32(0x7d)==0x082a0041 and s:read_u32(0x7f)==0x082d0043,'camera path signature')
        out=assert(io.open('world-camera.csv','w'))
        out:write('frame,x,y,z,m0,m1,m2,m3,m4,m5,m6,m7,m8\n')
        adc=assert(io.open('world-adc.csv','w'));adc:write('frame,time,pc,value\n')
        table.insert(taps,s:install_read_tap(0x993000,0x993000,'world_actual_adc',function(o,d,m)
            adc:write(string.format('%d,%.12f,%x,%x\n',frame,emu.time(),cpu.state.PC.value,d))
        end))
    end
    if out and n<=last then
        local p=s:read_u32(0x41);local m=s:read_u32(0x43)
        assert(p<0x20000 and m>=0x809800 and m<0x809ff8,'camera pointers outside expected RAM')
        out:write(n)
        for i=0,2 do out:write(string.format(',%08x',s:read_u32(p+i))) end
        for i=0,8 do out:write(string.format(',%08x',s:read_u32(m+i))) end
        out:write('\n')
    end
    if n==last+1 then close() end
end

end)(),
(function()
-- Explicit, bounded World 2.4 DISTANCE EXPERIMENT, not a product patch.
-- Extend reciprocal lookup reads without overwriting adjacent game RAM.
-- Run with replay.py --probe-script, original widescreen case, no physical force.
local cpu = manager.machine.devices[':maincpu']
local space = cpu.spaces.program
assert(manager.machine.system.name == 'crusnwld24', 'World 2.4 diagnostic only')
local first = tonumber(5900)
local last = tonumber(6140)
local far = tonumber(240000)
assert(first and last and first % 1 == 0 and last % 1 == 0
    and first >= 1 and last >= first and last-first <= 1800, 'invalid bounded interval')
assert(far and far % 16 == 0 and far > 80000 and far <= 240000, 'far must be a multiple of 16 in 80016..240000')
local max_index = far // 16
local tap, out, count, applied = nil, nil, 0, false
local words = {{0x40,0x00013880,far},
    {0xae,0x04e31387,0x04e30000|max_index},{0xaf,0x54e31387,0x54e30000|max_index},
    {0x13a,0x04f21387,0x04f20000|max_index},{0x13b,0x55721387,0x55720000|max_index},
    {0x14d,0x04f21387,0x04f20000|max_index},{0x14e,0x55721387,0x55720000|max_index},
    {0x199,0x04f21387,0x04f20000|max_index},{0x19a,0x55721387,0x55720000|max_index},
    {0x677,0x04f21387,0x04f20000|max_index},{0x678,0x55721387,0x55720000|max_index}}
local pcs = {}
for _, pc in ipairs({0xb4,0x143,0x147,0x152,0x154,0x1a0,0x1a2,
    0x1df,0x1e3,0x1ea,0x1ec,0x21c,0x21e,0x50e,0x510,0x67e,0x680}) do pcs[pc]=true end
local function restore()
    if tap then tap:remove(); tap=nil end
    if applied then
        for _,w in ipairs(words) do
            if space:read_u32(w[1]) == w[3] then space:write_u32(w[1],w[2]) end
        end
        applied=false
    end
end
cruisn_world_projection_stop = emu.add_machine_stop_notifier(function()
    restore()
    if out then out:write('extended_reads='..count..'\n'); out:close() end
end)
return function(n)
    if n == first then
        for _,w in ipairs(words) do assert(space:read_u32(w[1])==w[2], 'projection patch guard') end
        assert(space:read_u32(0x4d)==0xb66f, 'World reciprocal base signature')
        out=assert(io.open('projection-distance.log','w'))
        local cache={}
        for i=5000,max_index do
            -- Original far tail is six-decimal 512/(16*i+1), with one rounding
            -- exception among 2,000 checked entries. Existing entries stay exact.
            local value=math.floor(512/(16*i+1)*1000000+0.5)/1000000
            local ieee=string.unpack('<I4',string.pack('<f',value))
            cache[i]=((((ieee>>23)-127)&255)<<24)|(ieee&0x7fffff)
        end
        tap=space:install_read_tap(0xb66f+5000,0xb66f+max_index,'extended_world_projection',function(o,d,m)
            local pc=cpu.state.PC.value
            if not pcs[pc] then return end
            if pc~=0xb4 and cpu.state.AR2.value~=0xb66f then return end
            count=count+1
            return cache[o-0xb66f]
        end)
        for _,w in ipairs(words) do space:write_u32(w[1],w[3]) end
        applied=true
        out:write(string.format('far_limit=%d; lookup_max=%d; first=%d; last=%d; original_ram_preserved=true\n',
            far,max_index,first,last))
    elseif n == last+1 then restore() end
end

end)(),
(function()
-- MUTATING diagnostic: test the World 2.4 pending-list lookahead itself.
-- Covers every pending object, not just verified mountain models. No production
-- recommendation is implied. The guest transfers objects, which remain active
-- after the bounded tap closes. Original projection/far checks remain unchanged.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 pending-list diagnostic only')
assert(os.getenv('MIDV_SCENERY_LEAD')=='0','disable selective native activation for this comparison')
local first=tonumber(5900)
local last=tonumber(6140)
local lead=tonumber(12)
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=240 and lead and lead%1==0 and lead>=0 and lead<=12,
    'invalid bounded pending-list experiment')
local frame,taps,out,reads=0,{},nil,0
local function close()
    for _,t in ipairs(taps) do t:remove() end;taps={}
    if out then out:close();out=nil end
end
cruisn_pending_distance_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==first then
        assert(s:read_u32(0x7b50)==0x0224d58c and s:read_u32(0x7b51)==0x04a4d584
            and s:read_u32(0x7b58)==0x04800004 and s:read_u32(0x7b5c)==0x1ae03000
            and s:read_u32(0x7b68)==0x0840001b and s:read_u32(0xd58c)==11,
            'World pending-list signature mismatch')
        out=assert(io.open('pending-activation.csv','w'))
        out:write('frame,object,model,flags,radius,section,threshold,earlier\n')
        table.insert(taps,s:install_read_tap(0xd58c,0xd58c,'pending_lookahead',function(o,d,m)
            if cpu.state.PC.value~=0x7b51 then return end
            assert(d==11,'pending lookahead changed during experiment')
            reads=reads+1
            return d+lead
        end))
        table.insert(taps,s:install_write_tap(0x10800,0x1ffff,'pending_transfers',function(o,d,m)
            if cpu.state.PC.value~=0x7b5e then return end
            local object=cpu.state.AR0.value
            if object<0x10800 or object>=0x20000-27 or o~=object+14 then return end
            -- The only Lua read tap covers D58C; these reads cannot re-enter it.
            local model=s:read_u32(object+13)
            local radius=s:read_u32(object+19)
            local section=s:read_u32(object+27)&0xffff
            local threshold=cpu.state.R4.value
            out:write(string.format('%d,%x,%x,%x,%d,%d,%d,%d\n',frame,object,model,d,
                radius,section,threshold,section>threshold-lead and 1 or 0))
        end))
    elseif n==last+1 then
        close();assert(reads>0,'pending-list comparison was not observed')
    end
end

end)(),
(function()
-- Bounded read-only World 2.4 admission -> submitted polygon provenance.
-- Join only object IDs seen at the far gate in this frame, never a stale model.
local cpu=manager.machine.devices[':maincpu']; local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24', 'World 2.4 provenance only')
local first=tonumber(5900)
local last=tonumber(6140)
assert(first and last and first%1==0 and last%1==0 and first>=1
    and last>=first and last-first<=240, 'invalid bounded scenery interval')
local frame,page,pending,taps,admitted=0,0,{},{},{}
local draws,objects,count=nil,nil,0
local function signed(n) return n>=0x80000000 and n-0x100000000 or n end
local function close()
    for _,t in ipairs(taps) do t:remove() end; taps={}
    if draws then draws:close();draws=nil end
    if objects then objects:close();objects=nil end
end
cruisn_scenery_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n; admitted={}
    if n==first then
        assert(s:read_u32(0xa0)==0x04a30040 and s:read_u32(0x9c)>>16==0x1529,
            'World object path signature mismatch')
        local selected=s:read_u32(0x9c)&0xffff
        draws=assert(io.open('scenery-draws.csv','w'))
        objects=assert(io.open('scenery-objects.csv','w'))
        draws:write('frame,pc,page,object,model,matched,flags,palette,x0,y0,x1,y1,x2,y2,x3,y3,uv0,uv1,uv2,uv3,texture,word15\n')
        objects:write('frame,object,model,object_flags,depth_minus_radius,radius,far_limit\n')
        page=s:read_u32(0x980040)
        table.insert(taps,s:install_read_tap(0x40,0x40,'scenery_admission',function(o,d,m)
            if cpu.state.PC.value~=0xa1 then return end
            local id=cpu.state.AR0.value
            local model=s:read_u32(selected)
            admitted[id]=model
            objects:write(string.format('%d,%x,%x,%x,%d,%d,%d\n',frame,id,model,
                s:read_u32(id+14),signed(cpu.state.R3.value),signed(cpu.state.R4.value),d))
        end))
        table.insert(taps,s:install_write_tap(0x980040,0x980040,'scenery_page',function(o,d,m) page=d end))
        table.insert(taps,s:install_write_tap(0x600000,0x600000,'scenery_words',function(o,d,m)
            if #pending<16 then table.insert(pending,d&0xffff) end
        end))
        table.insert(taps,s:install_read_tap(0x980083,0x980083,'scenery_trigger',function(o,d,m)
            if #pending>=15 then
                local pc=cpu.state.PC.value
                -- Verified World slow polygon path pushes AR0 onto its stack.
                local id=pc==0x333 and s:read_u32(cpu.state.SP.value) or cpu.state.AR0.value
                local model=admitted[id]
                draws:write(string.format('%d,%x,%d,%x,%x,%d',frame,pc,page,id,model or 0,model and 1 or 0))
                for i=1,16 do draws:write(','..(pending[i] or 0)) end
                draws:write('\n'); count=count+1
            end
            pending={}
        end))
    elseif n==last+1 then close(); assert(count>0,'no scenery submissions captured') end
end

end)()
}
return function(frame) for _,f in ipairs(callbacks) do f(frame) end end
