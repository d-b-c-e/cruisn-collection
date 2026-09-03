-- inputprobe.lua - print the raw values MAME reads for the analog ports
-- (wheel, gas, brake) twice a second for PROBE_SECONDS (default 15), then
-- exit. Diagnoses "the game thinks the brake is pressed" style problems:
-- run with -window so the real devices are read (headless has none).
--
--   PROBE_SECONDS=15 vunit crusnusa -window -autoboot_script lua/inputprobe.lua
--
-- Output lines (stdout): "probe t=SECONDS WHEEL=v ACCEL=v BRAKE=v" - values
-- are the port reads (0..255; pedals rest at 0x00, wheel centre 0x80).

local secs = tonumber(os.getenv("PROBE_SECONDS") or "15")
local ports = {}
local count = 0

local function find_ports()
    local ioport = manager.machine.ioport
    for tag, port in pairs(ioport.ports) do
        if tag == ":WHEEL" or tag == ":ACCEL" or tag == ":BRAKE" or
           tag == ":ANALOG3" or tag == ":ANALOG2" or tag == ":ANALOG1" then
            ports[tag] = port
        end
    end
    local names = {}
    for tag, _ in pairs(ports) do names[#names + 1] = tag end
    table.sort(names)
    emu.print_info("inputprobe: ports " .. table.concat(names, " "))
end

emu.register_frame_done(function()
    count = count + 1
    if count == 1 then find_ports() end
    if count % 30 == 0 then
        local parts = {}
        local names = {}
        for tag, _ in pairs(ports) do names[#names + 1] = tag end
        table.sort(names)
        for _, tag in ipairs(names) do
            parts[#parts + 1] = string.format("%s=%d", tag:sub(2), ports[tag]:read())
        end
        emu.print_info(string.format("probe t=%.1f %s", count / 57.0, table.concat(parts, " ")))
    end
    if count >= secs * 57 then
        manager.machine:exit()
    end
end)
