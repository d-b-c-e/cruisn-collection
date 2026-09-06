-- Bounded V-Unit DMA provenance, for replay.py --probe-script. No mutation.
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces.program
local rom=manager.machine.system.name
assert(rom=='crusnusa' or rom=='crusnwld' or rom=='crusnwld24' or rom=='offroadc', 'V-Unit sets only')
local first=tonumber(os.getenv('CRUISN_DMA_FIRST') or '1540')
local last=tonumber(os.getenv('CRUISN_DMA_LAST') or '1561')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=240,'invalid DMA interval')
local frame,page,pending,taps,out,count=0,0,{},{},nil,0
local function close()
    for _,t in ipairs(taps) do t:remove() end
    taps={}
    if out then out:close();out=nil end
end
cruisn_dma_window_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==first then
        out=assert(io.open('dma-window.csv','w'))
        out:write('frame,pc,page,flags,palette,x0,y0,x1,y1,x2,y2,x3,y3,uv0,uv1,uv2,uv3,texture,word15,ar2,r1\n')
        page=s:read_u32(0x980040)
        table.insert(taps,s:install_write_tap(0x980040,0x980040,'dma_window_page',function(o,d,m) page=d end))
        table.insert(taps,s:install_write_tap(0x600000,0x600000,'dma_window_words',function(o,d,m)
            if #pending<16 then table.insert(pending,d&0xffff) end
        end))
        table.insert(taps,s:install_read_tap(0x980083,0x980083,'dma_window_trigger',function(o,d,m)
            if #pending>=15 then
                pending[16]=pending[16] or 0
                out:write(string.format('%d,%x,%d',frame,cpu.state.PC.value,page))
                for _,v in ipairs(pending) do out:write(','..v) end
                out:write(string.format(',%x,%x\n',cpu.state.AR2.value,cpu.state.R1.value));count=count+1
            end
            pending={}
        end))
    elseif n==last+1 then
        close();assert(count>0,'no completed DMA records')
    end
end
