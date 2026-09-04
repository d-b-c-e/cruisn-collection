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
--   DIP_SET      "Wheel Invert=0"  set DIP/config fields by MAME name to a
--                                 raw value at boot (comma-separated)
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
-- GEAR_FRAME=N: hold the 1st-gear button (IPT_BUTTON2 on V-Unit/Exotica)
-- from frame N on - does a shifter position pick MANUAL on Exotica's
-- TRANS SELECT screen?
local gear_frame = tonumber(os.getenv("GEAR_FRAME") or "")
local gear_f = nil
-- PRESS_FRAMES="3210:P1_BUTTON5,3300:START1": press any input type token
-- at a frame (held 30 frames) - brute-forcing which control a screen wants
local PRESS_HOLD = tonumber(os.getenv("PRESS_HOLD") or "30")   -- frames held (menus auto-repeat: use ~3)
-- FORCE_FRAMES="3225:IN1:4096,...": press the field with that mask in that
-- port tag (":IN1") at a frame, held PRESS_HOLD frames - reaches bits with
-- no bindable input type (IPT_UNKNOWN), for hunting mis-mapped lines
local forces = {}
for fr, tag, mask in (os.getenv("FORCE_FRAMES") or ""):gmatch("(%d+):(%w+):(%d+)") do
    forces[#forces + 1] = {frame = tonumber(fr), tag = ":" .. tag, mask = tonumber(mask), field = nil}
end
local presses = {}
for fr, tok in (os.getenv("PRESS_FRAMES") or ""):gmatch("(%d+):([%w_]+)") do
    presses[#presses + 1] = {frame = tonumber(fr), token = tok, field = nil}
end
local coin_f, start_f, gas_f, wheel_f = nil, nil, nil, nil
local sweep = {}
for fr, v in (os.getenv("WHEEL_SWEEP") or ""):gmatch("(%d+):(%d+)") do
    sweep[tonumber(fr)] = tonumber(v)
end

-- DIP_SET="Wheel Invert=0,Cabinet=1024": set DIP switch / configuration
-- fields by their MAME name to a raw value at boot (ioport_field.user_value).
-- Lets an undocumented DIP be tested without a cfg file or the UI.
local dipset = {}
for name, val in (os.getenv("DIP_SET") or ""):gmatch("([^=,]+)=(%d+)") do
    dipset[name:gsub("^%s+", ""):gsub("%s+$", "")] = tonumber(val)
end

local function apply_dips()
    local ioport = manager.machine.ioport
    for tag, port in pairs(ioport.ports) do
        for name, f in pairs(port.fields) do
            local want = dipset[name]
            if want ~= nil then
                local before = f.user_value
                f.user_value = want
                emu.print_info(string.format(
                    "coinup.lua: DIP %s%s %q: %d -> %d (mask %d)",
                    tag, "", name, before, f.user_value, f.mask))
            end
        end
    end
end

local function find_fields()
    local ioport = manager.machine.ioport
    for tag, port in pairs(ioport.ports) do
        for name, f in pairs(port.fields) do
            if f.type == ioport:token_to_input_type("COIN1") then
                coin_f = f
            elseif f.type == ioport:token_to_input_type("START1") then
                start_f = f
            elseif tag == ":ACCEL" or (tag == ":ANALOG2" and not gas_f) then
                gas_f = f            -- V-Unit :ACCEL; Exotica gas on :ANALOG2
            elseif f.type == ioport:token_to_input_type("P1_BUTTON2") and not gear_f then
                gear_f = f
            elseif tag == ":WHEEL" or (tag == ":ANALOG3" and not wheel_f) then
                wheel_f = f          -- V-Unit :WHEEL; Exotica steers on :ANALOG3
            end
            for _, pr in ipairs(presses) do
                if f.type == ioport:token_to_input_type(pr.token) then
                    pr.field = f
                end
            end
            for _, fo in ipairs(forces) do
                if tag == fo.tag and f.mask == fo.mask then
                    fo.field = f
                end
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
    if count == 1 then find_fields(); apply_dips() end
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
    for _, fo in ipairs(forces) do
        if fo.field and count == fo.frame then
            fo.field:set_value(1)
            emu.print_info("coinup.lua: force " .. fo.tag .. " mask " .. fo.mask .. " @" .. count)
        elseif fo.field and count == fo.frame + PRESS_HOLD then
            fo.field:clear_value()
        elseif count == fo.frame and not fo.field then
            emu.print_info("coinup.lua: force " .. fo.tag .. " mask " .. fo.mask .. " NOT FOUND")
        end
    end
    for _, pr in ipairs(presses) do
        if pr.field and count == pr.frame then
            pr.field:set_value(1)
            emu.print_info("coinup.lua: " .. pr.token .. " down @" .. count)
        elseif pr.field and count == pr.frame + PRESS_HOLD then
            pr.field:clear_value()
        end
    end
    if gear_frame and count == gear_frame and gear_f then
        gear_f:set_value(1)
        emu.print_info("coinup.lua: GEAR1 held @" .. count)
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
