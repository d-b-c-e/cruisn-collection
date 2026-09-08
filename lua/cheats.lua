-- Apply named selections through MAME's cheat engine, never a second evaluator.
local directory = assert(os.getenv('MIDV_CHEATS'))
local settings = assert(loadfile(directory .. '/settings.lua'))()
assert(settings.rom == emu.romname(), 'Cheat settings belong to another ROM revision')
local count, previous = 0, {}
local log = assert(io.open(directory .. '/events.csv', 'w'))
log:write('frame,index,state\n')
local function tick()
    count = count + 1
    if count == 1 then
        local entries = manager:cheat_entries()
        for _, request in ipairs(settings.entries) do
            local entry = assert(entries[request.index], 'Missing imported cheat')
            assert(entry.description == request.description, 'Cheat catalog changed')
            assert(entry.kind == 'toggle' or entry.kind == 'parameter', 'One-shot cheat cannot be selected before a race')
            assert(request.steps >= 1 and request.steps <= 64, 'Invalid cheat selection')
            manager:cheat_command(request.index, request.description, 'off')
            for _ = 1, request.steps do
                assert(manager:cheat_command(request.index, request.description, 'next'), 'Cheat choice unavailable')
            end
        end
    end
    for _, entry in ipairs(manager:cheat_entries()) do
        local state = tostring(entry.state):gsub('[\r\n]', ' ')
        if previous[entry.index] ~= state then
            log:write(string.format('%d,%d,"%s"\n', count, entry.index, state:gsub('"','""')))
            previous[entry.index] = state
            log:flush()
        end
    end
end
emu.register_stop(function() log:close() end)
if not os.getenv('SNAP_SESSION_LOG') then
    local failed = false
    emu.register_frame_done(function()
        if failed then return end
        local ok, reason = pcall(tick)
        if not ok then failed = true; emu.print_error('cheats.lua: failed: '..tostring(reason)); manager.machine:exit() end
    end)
end
return tick
