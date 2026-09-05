-- Record evidence at emulated frames. Never injects input: MAME INP owns replay.
-- Keep the notifier subscriptions alive for the lifetime of this script.
local count = 0
local last_emulated = -1
local every = tonumber(os.getenv("SNAP_EVERY")) or 60
local stop_frame = tonumber(os.getenv("SNAP_STOP")) or 0
local log_path = assert(os.getenv("SNAP_SESSION_LOG"), "SNAP_SESSION_LOG required")
local log = assert(io.open(log_path, "w"))
local tags = {}
for tag, _ in pairs(manager.machine.ioport.ports) do table.insert(tags, tag) end
table.sort(tags)
log:write("frame,emulated_seconds,host_seconds,speed_percent")
for _, tag in ipairs(tags) do log:write("," .. tag) end
log:write("\n")
local started = emu.osd_ticks()

emu.register_frame_done(function()
    if emu.time() == last_emulated then return end -- host redraw while paused
    last_emulated = emu.time()
    count = count + 1
    local host = (emu.osd_ticks() - started) / emu.osd_ticks_per_second()
    log:write(string.format("%d,%.12f,%.9f,%.6f", count, emu.time(), host,
                            manager.machine.video.speed_percent))
    for _, tag in ipairs(tags) do
        log:write(string.format(",%u", manager.machine.ioport.ports[tag]:read()))
    end
    log:write("\n")
    if count % every == 0 then
        local err = manager.machine.screens[":screen"]:snapshot(
            string.format("frame_%08d.png", count))
        if err then
            emu.print_error("session.lua: snapshot failed: " .. tostring(err))
            manager.machine:exit()
        else
            emu.print_info(string.format("session.lua: snapshot at frame %d", count))
        end
        log:flush()
    end
    if stop_frame > 0 and count >= stop_frame then manager.machine:exit() end
end)

-- A top-level local can be collected once autoboot returns. Retain the RAII
-- subscription in the Lua global table until machine stop has run.
cruisn_session_stop_subscription = emu.add_machine_stop_notifier(function()
    log:flush()
    log:close()
    emu.print_info(string.format("session.lua: stopped at frame %d", count))
end)
