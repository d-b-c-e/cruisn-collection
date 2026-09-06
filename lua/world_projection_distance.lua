-- Explicit, bounded World 2.4 DISTANCE EXPERIMENT, not a product patch.
-- Extend reciprocal lookup reads without overwriting adjacent game RAM.
-- Run with replay.py --probe-script, original widescreen case, no physical force.
local cpu = manager.machine.devices[':maincpu']
local space = cpu.spaces.program
assert(manager.machine.system.name == 'crusnwld24', 'World 2.4 diagnostic only')
local first = tonumber(os.getenv('CRUISN_DISTANCE_FIRST') or '2058')
local last = tonumber(os.getenv('CRUISN_DISTANCE_LAST') or '2061')
local far = tonumber(os.getenv('CRUISN_DISTANCE_FAR') or '100000')
assert(first and last and first % 1 == 0 and last % 1 == 0
    and first >= 1 and last >= first and last-first <= 1800, 'invalid bounded interval')
assert(far and far % 16 == 0 and far > 80000 and far <= 160000, 'far must be a multiple of 16 in 80016..160000')
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
