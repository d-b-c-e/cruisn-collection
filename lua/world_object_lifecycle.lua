-- Bounded, read-only World 2.4/2.5 object admission and model-selection trace.
-- Intended for replay.py --probe-script; guards are checked before taps exist.
local cpu = manager.machine.devices[':maincpu']
local space = cpu.spaces.program
local first = tonumber(os.getenv('CRUISN_OBJECT_FIRST') or '1800')
local last = tonumber(os.getenv('CRUISN_OBJECT_LAST') or '3600')
assert(manager.machine.system.name == 'crusnwld24' or manager.machine.system.name == 'crusnwld')
assert(first and last and first % 1 == 0 and last % 1 == 0 and first >= 1
       and last >= first and last - first <= 3600, 'invalid bounded trace interval')
local frame, tap, out = 0, nil, nil
local function signed(n) return n >= 0x80000000 and n - 0x100000000 or n end
cruisn_world_lifecycle_stop = emu.add_machine_stop_notifier(function()
    if tap then tap:remove() end
    if out then out:close() end
end)
return function(n)
    frame = n
    if n == first then
        assert(space:read_u32(0x94) == 0x04e22710
           and space:read_u32(0x9a) == 0x04e23a98
           and space:read_u32(0xa0) == 0x04a30040
           and (space:read_u32(0xc0) == 0x6a270289 or space:read_u32(0xc0) == 0x72070048),
           'World object path signature mismatch')
        local selected = space:read_u32(0x9c) & 0xffff
        assert((space:read_u32(0x9c) >> 16) == 0x1529, 'model store signature mismatch')
        out = assert(io.open('lifecycle.csv', 'w'))
        out:write('frame,object,model,flags,depth_minus_radius,radius,far_limit,x,y,z,base_model,mid_model,far_model\n')
        tap = space:install_read_tap(0x40, 0x40, 'world_object_far_gate', function(offset, data, mask)
            if cpu.state.PC.value ~= 0xa1 then return end
            local id = cpu.state.AR0.value
            local base = space:read_u32(id + 13)
            out:write(string.format('%d,%x,%x,%x,%d,%d,%d,%x,%x,%x,%x,%x,%x\n',
                frame, id, space:read_u32(selected), space:read_u32(id + 14),
                signed(cpu.state.R3.value), signed(cpu.state.R4.value), data,
                space:read_u32(id + 1), space:read_u32(id + 2), space:read_u32(id + 3),
                base, space:read_u32(base - 3), space:read_u32(base - 4)))
        end)
    elseif n == last + 1 and tap then
        tap:remove(); tap = nil
        out:flush()
    end
end
