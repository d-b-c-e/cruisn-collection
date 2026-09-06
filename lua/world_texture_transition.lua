-- Bounded World transmission diagnostic. Separate dense native frames, completed
-- DMA records, and texture-write block counts; never changes inputs/game memory.
local cpu = manager.machine.devices[':maincpu']
local space = cpu.spaces.program
assert(manager.machine.system.name == 'crusnwld24', 'World 2.4 diagnostic only')
local frame, page, pending, taps, blocks = 0, 0, {}, {}, {}
local draws, writes, draw_count = nil, nil, 0
local function flush_blocks()
    if not writes then return end
    for address, row in pairs(blocks) do
        writes:write(string.format('%d,%x,%x,%x,%d\n',frame,address,row[1],row[2],row[3]))
    end
    blocks = {}
end
cruisn_transition_stop = emu.add_machine_stop_notifier(function()
    for _, tap in ipairs(taps) do tap:remove() end
    flush_blocks()
    if draws then draws:close(); writes:close() end
end)
return function(n)
    flush_blocks(); frame = n
    if n == 1280 then
        draws = assert(io.open('transition-quads.csv','w'))
        draws:write('frame,pc,page,flags,palette,x0,y0,x1,y1,x2,y2,x3,y3,uv0,uv1,uv2,uv3,texture,word15\n')
        writes = assert(io.open('transition-writes.csv','w'))
        writes:write('frame,block,first_pc,last_pc,words\n')
        page = space:read_u32(0x980040)
        table.insert(taps,space:install_write_tap(0x980040,0x980040,'transition_page',function(o,d,m) page=d end))
        table.insert(taps,space:install_write_tap(0x600000,0x600000,'transition_dma',function(o,d,m)
            if #pending < 16 then table.insert(pending,d & 0xffff) end
        end))
        table.insert(taps,space:install_read_tap(0x980083,0x980083,'transition_trigger',function(o,d,m)
            -- World often submits only the 15 used words; word 15 is unused.
            if #pending >= 15 then
                pending[16] = pending[16] or 0
                draw_count = draw_count + 1
                draws:write(string.format('%d,%x,%d',frame,cpu.state.PC.value,page))
                for _,v in ipairs(pending) do draws:write(','..v) end
                draws:write('\n')
            end
            pending = {}
        end))
        table.insert(taps,space:install_write_tap(0xa00000,0xbfffff,'transition_texture',function(o,d,m)
            local block = o & ~255
            local pc = cpu.state.PC.value
            local row = blocks[block]
            if row then row[2]=pc; row[3]=row[3]+1 else blocks[block]={pc,pc,1} end
        end))
    end
    if n >= 1280 and n <= 1380 then
        local w,h = manager.machine.video:snapshot_size()
        local file = assert(io.open(string.format('transition_%08d.raw',n),'wb'))
        assert(file:write(string.pack('<c8I4I4','CRSNRAW1',w,h),manager.machine.video:snapshot_pixels()))
        file:close()
    end
    if n == 1381 then
        for _,tap in ipairs(taps) do tap:remove() end
        taps={}; draws:flush(); writes:flush()
        assert(draw_count > 0, 'no completed DMA records: diagnostic is incomplete')
    end
end
