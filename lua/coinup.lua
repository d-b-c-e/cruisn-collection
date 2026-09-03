-- coinup.lua - snap.lua plus scripted coin/start injection, for reaching
-- gameplay-only screens (track select map, continue screen) headless.
--
-- Env:
--   SNAP_FRAMES  "1000,1200,..."  frames to snapshot (as snap.lua)
--   COIN_FRAMES  "600,700,800"    frames to press COIN1 (held 10 frames)
--   START_FRAMES "900"            frames to press START1 (held 10 frames)
--   GAS_FRAME    "3800"           frame to floor the gas pedal (held to
--                                 exit; drives the car so world streaming
--                                 and distance culling actually exercise)
--   WHEEL_SWEEP  "4000:128,4300:64,..."  frame:value pairs - park the
--                                 steering field (:WHEEL, 0-255, 128 =
--                                 center) at a value from that frame on;
--                                 with MIDV_FFB_TRACE this measures the
--                                 game's force-vs-position law headless
--
-- Field writes use ioport_field:set_value()/clear_value() - unlike
-- keybd_event probing (which never reaches rawinput headless), these land
-- directly in the port read path and work with -video none.

local function parse(env)
    local t = {}
    for n in (os.getenv(env) or ""):gmatch("(%d+)") do
        t[#t + 1] = tonumber(n)
    end
    return t
end

local snaps, coins, starts = {}, parse("COIN_FRAMES"), parse("START_FRAMES")
local last = 0
for n in (os.getenv("SNAP_FRAMES") or ""):gmatch("(%d+)") do
    snaps[tonumber(n)] = true
    if tonumber(n) > last then last = tonumber(n) end
end

local HOLD = 10
local gas_frame = tonumber(os.getenv("GAS_FRAME") or "")
local coin_f, start_f, gas_f, wheel_f = nil, nil, nil, nil
local sweep = {}
for fr, v in (os.getenv("WHEEL_SWEEP") or ""):gmatch("(%d+):(%d+)") do
    sweep[tonumber(fr)] = tonumber(v)
end

local function find_fields()
    local ioport = manager.machine.ioport
    for tag, port in pairs(ioport.ports) do
        for name, f in pairs(port.fields) do
            if f.type == ioport:token_to_input_type("COIN1") then
                coin_f = f
            elseif f.type == ioport:token_to_input_type("START1") then
                start_f = f
            elseif tag == ":ACCEL" then
                gas_f = f
            elseif tag == ":WHEEL" or (tag == ":ANALOG3" and not wheel_f) then
                wheel_f = f          -- V-Unit :WHEEL; Exotica steers on :ANALOG3
            end
        end
    end
    emu.print_info(string.format("coinup.lua: coin=%s start=%s gas=%s",
        coin_f and "found" or "MISSING", start_f and "found" or "MISSING",
        gas_f and "found" or "MISSING"))
end

local count = 0

emu.register_frame_done(function()
    count = count + 1
    if count == 1 then find_fields() end
    for _, cf in ipairs(coins) do
        if count == cf and coin_f then
            coin_f:set_value(1)
            emu.print_info("coinup.lua: COIN down @" .. count)
        elseif count == cf + HOLD and coin_f then
            coin_f:clear_value()
            emu.print_info("coinup.lua: COIN up @" .. count)
        end
    end
    for _, sf in ipairs(starts) do
        if count == sf and start_f then
            start_f:set_value(1)
            emu.print_info("coinup.lua: START down @" .. count)
        elseif count == sf + HOLD and start_f then
            start_f:clear_value()
            emu.print_info("coinup.lua: START up @" .. count)
        end
    end
    if gas_frame and count == gas_frame and gas_f then
        gas_f:set_value(0xff)
        emu.print_info("coinup.lua: GAS floored @" .. count)
    end
    if sweep[count] and wheel_f then
        wheel_f:set_value(sweep[count])
        emu.print_info("coinup.lua: WHEEL = " .. sweep[count] .. " @" .. count)
    end
    if snaps[count] then
        manager.machine.video:snapshot()
    end
    -- no SNAP_FRAMES: never self-exit (the harness's -seconds_to_run
    -- bounds the run) - snap.lua's default schedule would exit at frame
    -- 2400, which is before any coined-up screen exists
    if last > 0 and count >= last then
        manager.machine:exit()
    end
end)
