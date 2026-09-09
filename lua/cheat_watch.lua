-- Read-only observations for the live-cheat loader's frame-stamped action test.
-- Selection/activation is performed ONLY by cheats.lua through MAME's engine.
local rom = emu.romname()
local address = assert(({crusnusa=0xe634,crusnwld24=0xebe4,crusnwld=0xebde,
    offroadc=0x1d131,crusnexo=0x1038})[rom], 'Unsupported cheat probe ROM')
local p = manager.machine.devices[':maincpu'].spaces.program
local log = assert(io.open('cheat-probe.csv','w'))
log:write('frame,timer,timer_high,state\n')
-- Exact-revision observations only. These values never write guest memory or
-- evaluate XML; MAME's imported scripts own all modification and restoration.
local code, words
if os.getenv('CHEAT_PROBE_RESTORE') == '1' then
    words=assert(({crusnusa={[0x2a74]=0x0c800000,[0x2f22]=0x6a000008,[0x2f68]=0x0c800000,[0x2f69]=0x0c800000},
        crusnwld24={}, crusnwld={[0x1d51]=0x6a000008,[0x1d9a]=0x0c800000,[0x2015]=0x6a000002},
        offroadc={[0x1097]=0x6a000065,[0xb10b]=0x78800000,[0xb72e]=0x6a000002},
        crusnexo={[0x3dd8]=0x6a000008,[0x3e1d]=0x0c800000,[0x40c5]=0x6a000002}})[rom])
    code=assert(io.open('cheat-code-probe.csv','w'))
    code:write('frame,address,value,expected\n')
end
emu.register_stop(function() log:close(); if code then code:close() end end)
return function(frame)
    if code and ({[2699]=true,[2710]=true,[2799]=true,[2800]=true,[2801]=true,[3100]=true})[frame] then
        local addresses={}; for address in pairs(words) do addresses[#addresses+1]=address end
        table.sort(addresses)
        for _,address in ipairs(addresses) do
            code:write(string.format('%d,%x,%x,%x\n',frame,address,p:read_u32(address),words[address]))
        end
    end
    if frame >= 2500 and frame <= 3300 then
        assert(manager:cheat_entries()[1].description == 'Infinite Time')
        local low = p:read_u32(address) & 255
        local high = rom == 'offroadc' and (p:read_u32(address+1) & 255) or 0
        log:write(string.format('%d,%d,%d,%s\n',frame,low,high,manager:cheat_entries()[1].state))
    end
    if frame == 3300 then log:flush(); print('CHEAT PROBE COMPLETE') end
end
