-- Apply named selections through MAME's cheat engine, never a second evaluator.
local directory = assert(os.getenv('MIDV_CHEATS'))
local settings = assert(loadfile(directory .. '/settings.lua'))()
assert(settings.rom == emu.romname(), 'Cheat settings belong to another ROM revision')
local count, previous = 0, {}
local live = settings.live_protocol == 1
local menu_supported = live and manager.cheat_menu_publish and manager.cheat_menu_take
local positions, catalog = {}, {}
local actions, playback, next_action = {}, false, 1
local action_log
if live then
    for _, entry in ipairs(settings.catalog) do catalog[entry.index] = entry end
    local source = io.open(directory .. '/replay-actions.csv', 'r')
    if source then
        playback = true
        assert(source:read('*l') == 'frame,index,steps,activate', 'Invalid cheat action header')
        local last = 1
        for line in source:lines() do
            local frame, index, steps, activate = line:match('^(%d+),(%d+),(%d+),([01])$')
            frame, index, steps = tonumber(frame), tonumber(index), tonumber(steps)
            assert(frame and frame >= last and frame <= 100000000 and #actions < 100000, 'Invalid cheat action frame')
            assert(catalog[index] and steps < #catalog[index].choices, 'Invalid cheat action selection')
            actions[#actions + 1] = {frame=frame, index=index, steps=steps, activate=activate == '1'}
            last = frame
        end
        source:close()
    end
    action_log = assert(io.open(directory .. '/actions.csv', 'w'))
    action_log:write('frame,index,steps,activate\n')
end
local function execute(request, entries)
    local row = assert(catalog[request.index], 'Unknown live cheat')
    local entry = assert(entries[request.index], 'Missing live cheat')
    assert(entry.kind ~= 'text' and row.description == entry.description, 'Live cheat catalog changed')
    assert(request.steps >= 0 and request.steps < #row.choices, 'Invalid live cheat value')
    local shot = entry.kind == 'oneshot' or entry.kind == 'oneshot_parameter'
    assert(not request.activate or shot, 'Only one-shot entries support activation')
    if entry.kind ~= 'oneshot' then
        local position = positions[entry.index] or 0
        if request.steps == 0 then
            manager:cheat_command(entry.index, entry.description, 'off')
        else
            while position ~= request.steps do
                local direction = position < request.steps and 1 or -1
                assert(manager:cheat_command(entry.index, entry.description,
                    direction == 1 and 'next' or 'previous'), 'Live cheat choice unavailable')
                position = position + direction
            end
        end
        positions[entry.index] = request.steps
    end
    if request.activate then
        assert(manager:cheat_command(entry.index, entry.description, 'activate'), 'Live cheat activation failed')
    end
    action_log:write(string.format('%d,%d,%d,%d\n', count, request.index, request.steps, request.activate and 1 or 0))
    action_log:flush()
end
local function publish(entries)
    local rows = {}
    for _, entry in ipairs(entries) do
        local row = assert(catalog[entry.index], 'Imported cheat catalog has missing entries')
        assert(entry.kind == 'text' or row.description == entry.description, 'Imported cheat catalog changed')
        rows[#rows + 1] = {index=entry.index,description=entry.description,comment=entry.comment,
            choices=row.choices,kind=entry.kind,steps=positions[entry.index] or 0}
    end
    assert(#rows == #settings.catalog, 'Imported cheat catalog length changed')
    if menu_supported then manager:cheat_menu_publish(rows, playback) end
end
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
            positions[request.index] = request.steps
        end
    end
    if live then
        local entries = manager:cheat_entries()
        local changed = false
        if playback then
            while actions[next_action] and actions[next_action].frame == count do
                execute(actions[next_action], entries); next_action = next_action + 1; changed = true
            end
        elseif menu_supported then
            for _, request in ipairs(manager:cheat_menu_take()) do execute(request, entries); changed = true end
        end
        if count == 1 or changed then publish(manager:cheat_entries()) end
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
emu.register_stop(function()
    log:close()
    if action_log then action_log:close() end
    if live then
        if menu_supported then manager:cheat_menu_publish({}, true) end
        assert(not playback or next_action > #actions, 'Playback ended before recorded cheat actions')
    end
end)
if not os.getenv('SNAP_SESSION_LOG') then
    local failed = false
    emu.register_frame_done(function()
        if failed then return end
        local ok, reason = pcall(tick)
        if not ok then failed = true; emu.print_error('cheats.lua: failed: '..tostring(reason)); manager.machine:exit() end
    end)
end
return tick
