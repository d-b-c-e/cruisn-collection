-- Read-only timer observations around native cheat commands. Exact arcade sets.
local rom = emu.romname()
local address = assert(({crusnusa=0xe634,crusnwld24=0xebe4,crusnwld=0xebde,
    offroadc=0x1d131,crusnexo=0x1038})[rom], 'Unsupported cheat probe ROM')
local p = manager.machine.devices[':maincpu'].spaces.program
local log = assert(io.open('cheat-probe.csv','w'))
log:write('frame,timer,timer_high,state\n')
local frame, failed = 0, false
emu.register_frame_done(function()
    if failed then return end
    local ok, reason = pcall(function()
        frame = frame + 1
        if frame == 1 then
            local rows = manager:cheat_entries()
            assert(#rows >= 3 and rows[1].description == 'Infinite Time')
            assert(not pcall(function() manager:cheat_command(0,'','next') end))
            assert(not pcall(function() manager:cheat_command(1,'stale description','next') end))
        end
        if frame == 2600 then assert(manager:cheat_command(1,'Infinite Time','next')) end
        if frame == 3000 then assert(manager:cheat_command(1,'Infinite Time','off')) end
        if frame >= 2500 then
            local low = p:read_u32(address) & 255
            local high = rom == 'offroadc' and (p:read_u32(address+1) & 255) or 0
            log:write(string.format('%d,%d,%d,%s\n',frame,low,high,manager:cheat_entries()[1].state))
        end
        if frame == 3300 then
            log:close(); print('CHEAT PROBE COMPLETE'); manager.machine:exit()
        end
    end)
    if not ok then failed = true; log:close(); emu.print_error('cheat_probe: failed: '..tostring(reason)); manager.machine:exit() end
end)
