-- transmission_probe.lua - headless input driver for the World manual/auto
-- investigation (rig bug G7 follow-up). Frame-scheduled via env vars:
--   TP_COIN=<frame>     pulse Coin 1 (skippable when free play is on)
--   TP_START=<frame>    pulse Start 1
--   TP_GEAR=<frame>     from this frame on, HOLD 1st Gear (0 = never)
--   TP_GAS=<f1,f2,...>  hold full gas for 30 frames starting at each f
--   SNAP_FRAMES=...     snapshot schedule (same as snap.lua)
--   TP_LAST=<frame>     exit frame
local function num(name) return tonumber(os.getenv(name) or "0") or 0 end
local coin_f = num("TP_COIN")
local start_f = num("TP_START")
local gear_f = num("TP_GEAR")
local last_f = num("TP_LAST")
local gas = {}
for n in (os.getenv("TP_GAS") or ""):gmatch("(%d+)") do
    gas[#gas + 1] = tonumber(n)
end
local snaps = {}
for n in (os.getenv("SNAP_FRAMES") or ""):gmatch("(%d+)") do
    snaps[tonumber(n)] = true
end

local ioport = manager.machine.ioport
local function field_by_mask(tag, mask)
    local port = ioport.ports[tag]
    if not port then return nil end
    for _, f in pairs(port.fields) do
        if f.mask == mask then return f end
    end
    return nil
end

local coin, start, gear1, accel
local function setv(f, v)
    if f then pcall(function() f:set_value(v) end) end
end
local count = 0
emu.register_frame_done(function()
    count = count + 1
    if count == 1 then
        coin = field_by_mask(":IN0", 0x0001)
        start = field_by_mask(":IN0", 0x0004)
        gear1 = field_by_mask(":IN0", 0x2000)
        accel = field_by_mask(":ACCEL", 0xff)
        emu.print_info(string.format("probe: fields coin=%s start=%s gear=%s gas=%s",
            tostring(coin ~= nil), tostring(start ~= nil),
            tostring(gear1 ~= nil), tostring(accel ~= nil)))
    end
    if coin_f > 0 then
        setv(coin, (count >= coin_f and count < coin_f + 10) and 1 or 0)
    end
    if start_f > 0 then
        setv(start, (count >= start_f and count < start_f + 10) and 1 or 0)
    end
    if gear_f > 0 then
        setv(gear1, count >= gear_f and 1 or 0)
    end
    local on = false
    for _, f in ipairs(gas) do
        if count >= f and count < f + 30 then on = true end
    end
    setv(accel, on and 0xff or 0)
    if count % 300 == 0 then
        emu.print_info(string.format("probe: heartbeat frame %d", count))
    end
    if snaps[count] then
        local ok, err = pcall(function() manager.machine.video:snapshot() end)
        emu.print_info(string.format("probe: snapshot at frame %d ok=%s %s",
            count, tostring(ok), tostring(err)))
    end
    if last_f > 0 and count >= last_f then
        manager.machine:exit()
    end
end)
