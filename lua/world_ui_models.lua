-- Read-only World 2.4 selected UI model/texture provenance.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24')
local frame,pending,taps,out=0,{},{},nil
local function close()
    for _,t in ipairs(taps) do t:remove() end;taps={}
    if out then out:close();out=nil end
end
cruisn_ui_models_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==900 then
        out=assert(io.open('ui-models.csv','w'))
        out:write('frame,pc,object,model,flags,texture,palette,x0,y0,x1,y1,x2,y2,x3,y3,sp,stack0,stack1,r6\n')
        table.insert(taps,s:install_write_tap(0x600000,0x600000,'ui_model_words',function(o,d,m)
            if #pending<16 then table.insert(pending,d&0xffff) end
        end))
        table.insert(taps,s:install_read_tap(0x980083,0x980083,'ui_model_trigger',function(o,d,m)
            if #pending>=15 and (pending[1]&0x300)==0x100 then
                local pc=cpu.state.PC.value;local sp=cpu.state.SP.value
                local object=(pc==0x333) and s:read_u32(sp) or cpu.state.AR0.value
                local model=object<0x20000 and s:read_u32(object+13) or 0
                out:write(string.format('%d,%x,%x,%x,%x,%x,%x',frame,pc,object,model,pending[1],pending[15],pending[2]))
                for i=3,10 do out:write(','..pending[i]) end
                out:write(string.format(',%x,%x,%x,%x\n',sp,s:read_u32(sp),s:read_u32(sp-1),cpu.state.R6.value))
            end
            pending={}
        end))
    elseif n==1401 then close() end
end
