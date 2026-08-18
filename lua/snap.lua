-- snap.lua - deterministic frame capture for the midvunit oracle harness.
--
-- Counts frames from machine start, snapshots the screen at fixed frame
-- numbers, then exits. Run the same invocation twice: identical snapshots
-- prove the attract sequence is a deterministic test oracle.
--
-- Frame numbers come from the env var SNAP_FRAMES ("300,600,1200"),
-- so the harness owns the schedule, not this file.

local frames = {}
do
    local spec = os.getenv("SNAP_FRAMES") or "300,600,1200,1800,2400"
    for n in spec:gmatch("(%d+)") do
        frames[tonumber(n)] = true
    end
end

local last = 0
for n in pairs(frames) do
    if n > last then last = n end
end

local count = 0

emu.register_frame_done(function()
    count = count + 1
    if frames[count] then
        manager.machine.video:snapshot()
        emu.print_info(string.format("snap.lua: snapshot at frame %d", count))
    end
    if count >= last then
        manager.machine:exit()
    end
end)
