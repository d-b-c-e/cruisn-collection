-- coinup.lua - snap.lua plus scripted coin/start injection, for reaching
-- gameplay-only screens (track select map, continue screen) headless.
--
-- Env:
--   SNAP_FRAMES  "1000,1200,..."  frames to snapshot (as snap.lua)
--   COIN_FRAMES  "600,700,800"    frames to press COIN1 (held 10 frames)
--   START_FRAMES "900"            frames to press START1 (held 10 frames)
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
local coin_f, start_f = nil, nil

local function find_fields()
    local ioport = manager.machine.ioport
    for tag, port in pairs(ioport.ports) do
        for name, f in pairs(port.fields) do
            if f.type == ioport:token_to_input_type("COIN1") then
                coin_f = f
            elseif f.type == ioport:token_to_input_type("START1") then
                start_f = f
            end
        end
    end
    emu.print_info(string.format("coinup.lua: coin=%s start=%s",
        coin_f and "found" or "MISSING", start_f and "found" or "MISSING"))
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
    if snaps[count] then
        manager.machine.video:snapshot()
    end
    if count >= last then
        manager.machine:exit()
    end
end)
