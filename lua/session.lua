-- Record evidence at emulated frames. Never injects input: MAME INP owns replay.
-- Keep the notifier subscriptions alive for the lifetime of this script.
local count = 0
local last_emulated = -1
local every = tonumber(os.getenv("SNAP_EVERY")) or 60
local stop_frame = tonumber(os.getenv("SNAP_STOP")) or 0
local log_path = assert(os.getenv("SNAP_SESSION_LOG"), "SNAP_SESSION_LOG required")
local raw_dir = os.getenv("SNAP_RAW_DIR")
local log = assert(io.open(log_path, "w"))
local tags = {}
for tag, _ in pairs(manager.machine.ioport.ports) do table.insert(tags, tag) end
table.sort(tags)
log:write("frame,emulated_seconds,host_seconds,speed_percent")
for _, tag in ipairs(tags) do log:write("," .. tag) end
log:write("\n")
local started = emu.osd_ticks()
local probe_path = os.getenv("SNAP_PROBE_SCRIPT")
local probe = probe_path and assert(loadfile(probe_path))() or nil

emu.register_frame_done(function()
    if emu.time() == last_emulated then return end -- host redraw while paused
    last_emulated = emu.time()
    count = count + 1
    if probe then probe(count) end
    local host = (emu.osd_ticks() - started) / emu.osd_ticks_per_second()
    log:write(string.format("%d,%.12f,%.9f,%.6f", count, emu.time(), host,
                            manager.machine.video.speed_percent))
    for _, tag in ipairs(tags) do
        log:write(string.format(",%u", manager.machine.ioport.ports[tag]:read()))
    end
    log:write("\n")
    if count % every == 0 then
        local err
        if raw_dir then
            -- Avoid PNG encoding on the emulation thread. The harness converts
            -- these immutable RGB32 frames after the process has exited.
            -- Use the snapshot render target, just like screen:snapshot().
            -- screen:pixels() can expose the other buffer of a double-buffered
            -- screen and therefore differs by a frame during motion.
            local width, height = manager.machine.video:snapshot_size()
            local pixels = manager.machine.video:snapshot_pixels()
            local out
            out, err = io.open(raw_dir .. string.format("/frame_%08d.raw", count), "wb")
            if out then
                local ok
                ok, err = out:write(string.pack("<c8I4I4", "CRSNRAW1", width, height), pixels)
                local closed, close_err = out:close()
                if not closed then err = close_err end
                if ok and closed then err = nil end
            end
        else
            err = manager.machine.screens[":screen"]:snapshot(
                string.format("frame_%08d.png", count))
        end
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
