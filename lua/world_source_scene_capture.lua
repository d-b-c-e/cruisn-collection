-- Capture World RAM and C31 camera operands at the actual host-scene read.
-- This diagnostic only reads memory. Saved files remain in the local replay.
local cpu = manager.machine.devices[':maincpu']
local space = cpu.spaces.program
local ram = assert(manager.machine.memory.shares[':ram_base'])
local texture = assert(manager.machine.memory.shares[':textureram'])
local palette = assert(manager.machine.memory.shares[':paletteram'])
local screen = manager.machine.screens[':screen']
local rom = manager.machine.system.name
assert(rom == 'crusnwld24' or rom == 'crusnwld', 'World source capture only')
assert(ram.size == 0x80000, 'unexpected World main RAM extent')
assert(texture.size == 0x800000 and palette.size == 0x20000,
       'unexpected World texture/palette RAM extent')
local target = tonumber(os.getenv('MIDV_GL_HOST_METADATA_FRAME'))
assert(target and target % 1 == 0 and target >= 1800 and target <= 12000,
       'explicit bounded host metadata frame required')
assert(os.getenv('MIDV_FFB') == '0', 'source capture requires disabled physical force')
local address = rom == 'crusnwld24' and 0x61ee or 0x658f
local saved, busy, failure = false, false, nil
local tap

local function dump(path, count, reader)
    local file = assert(io.open(path, 'wb'))
    local chunk = {}
    for i = 0, count-1 do
        chunk[#chunk+1] = string.pack('<I4', reader(i))
        if #chunk == 1024 then
            assert(file:write(table.concat(chunk)))
            chunk = {}
        end
    end
    if #chunk > 0 then assert(file:write(table.concat(chunk))) end
    assert(file:close())
end

tap = space:install_read_tap(address, address, 'world_source_scene', function()
    if busy or saved or failure or screen:frame_number() ~= target or
       cpu.state.PC.value ~= 0x6a then return end
    busy = true
    local ok, reason = pcall(function()
        local stem = string.format('world-source-%d', target)
        dump(stem..'-ram.bin', 0x20000, function(p) return ram:read_u32(4*p) end)
        dump(stem..'-fast.bin', 0x800, function(p) return space:read_u32(0x809800+p) end)
        dump(stem..'-textures.bin', texture.size/4,
             function(p) return texture:read_u32(4*p) end)
        dump(stem..'-palettes.bin', palette.size/4,
             function(p) return palette:read_u32(4*p) end)
        local file = assert(io.open(stem..'-receipt.csv', 'w'))
        assert(file:write('frame,pc,scene_address,rom\n'))
        assert(file:write(string.format('%d,%x,%x,%s\n', screen:frame_number(),
            cpu.state.PC.value, address, rom)))
        assert(file:close())
        saved = true
    end)
    busy = false
    if not ok then failure = tostring(reason) end
end)

local function close()
    if tap then tap:remove(); tap = nil end
end
cruisn_world_source_stop = emu.add_machine_stop_notifier(close)
return function()
    if failure then error(failure) end
    if screen:frame_number() >= target + 2 then
        close()
        assert(saved, 'World source scene did not reach requested frame')
    end
end
