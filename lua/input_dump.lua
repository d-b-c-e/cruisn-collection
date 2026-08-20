-- Diagnostic: dump every input device/item MAME sees + every port's
-- resolved binding, then exit. Driven by the support-bundle generator:
--   INPUT_DUMP=<outfile> vunit <rom> -autoboot_script lua/input_dump.lua
local out = io.open(os.getenv("INPUT_DUMP") or "input_dump.txt", "w")
local booted = false
emu.register_frame_done(function()
    local m = manager.machine
    if m.screens == nil then return end
    if booted then return end
    if m.time.seconds < 4 then return end   -- let device enumeration settle
    booted = true

    local input = m.input
    out:write("== input device classes ==\n")
    for cname, cls in pairs(input.device_classes) do
        out:write(string.format("class %s enabled=%s\n", cname, tostring(cls.enabled)))
        for idx, dev in pairs(cls.devices) do
            out:write(string.format("  device %s: name=%q id=%q\n",
                tostring(idx), dev.name, dev.id))
            local n = 0
            for _ in pairs(dev.items) do n = n + 1 end
            out:write(string.format("    item count: %d\n", n))
            for itemid, item in pairs(dev.items) do
                out:write(string.format("    item id=%s name=%q token=%q code_token=%q\n",
                    tostring(itemid), item.name, item.token,
                    input:code_to_token(item.code)))
            end
        end
    end

    out:write("== port field bindings ==\n")
    for tag, port in pairs(m.ioport.ports) do
        for fname, field in pairs(port.fields) do
            local seq = field:input_seq("standard")
            out:write(string.format("%s / %q -> %q\n", tag, fname,
                input:seq_to_tokens(seq)))
        end
    end
    out:close()
    m:exit()
end)
