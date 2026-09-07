-- MUTATING diagnostic, World 2.4 only. Admit one identified pending scenery
-- object one track-section comparison earlier. The guest performs its own list
-- transfer; no links, flags, asset data or projection instructions are written.
-- Earlier activation persists after this bounded tap closes. Not a product fix.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 activation experiment only')
local first=tonumber(os.getenv('CRUISN_ACTIVATION_FIRST') or '2970')
local last=tonumber(os.getenv('CRUISN_ACTIVATION_LAST') or '3040')
local object=tonumber(os.getenv('CRUISN_ACTIVATION_OBJECT') or '12668',16)
local model=tonumber(os.getenv('CRUISN_ACTIVATION_MODEL') or 'ccf288',16)
local lead=tonumber(os.getenv('CRUISN_ACTIVATION_LEAD') or '1')
local radii={ [0xccf288]=13906, [0xcb15f8]=33292, [0xcb171e]=31514,
    [0xcb1a8b]=26031, [0xcb2314]=19772, [0xcb21a2]=12790, [0xcb2375]=10935 }
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>=first
    and last-first<=240 and object and object>=0x10800 and object<0x17ff0
    and radii[model] and lead and lead%1==0 and lead>=1 and lead<=8,
    'unverified activation target or interval')
local frame,tap,out,count=0,nil,nil,0
local function close()
    if tap then tap:remove();tap=nil end
    if out then out:close();out=nil end
end
cruisn_scenery_early_activation_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==first then
        assert(s:read_u32(0x7b68)==0x0840001b and s:read_u32(0x7b69)==0x02e0ffff
            and s:read_u32(0x7b58)==0x04800004 and s:read_u32(0x7b5c)==0x1ae03000,
            'World pending-list activation signature mismatch')
        out=assert(io.open('scenery-early-activation.csv','w'))
        out:write('frame,object,model,section,effective_section,threshold,earlier\n')
        -- Narrow tap: model/flags/radius reads below cannot re-enter it.
        tap=s:install_read_tap(object+27,object+27,'earlier_scenery_section',function(o,d,m)
            if cpu.state.PC.value~=0x7b69 or cpu.state.AR0.value~=object
                or s:read_u32(object+13)~=model or s:read_u32(object+14)~=0x2000
                or s:read_u32(object+19)~=radii[model] then return end
            local section=d&0xffff
            if section<lead then return end
            local threshold=cpu.state.R4.value
            local earlier=section>threshold and section-lead<=threshold
            if earlier then count=count+1 end
            out:write(string.format('%d,%x,%x,%d,%d,%d,%d\n',frame,object,model,
                section,section-lead,threshold,earlier and 1 or 0))
            return (d&0xffff0000)|(section-lead)
        end)
    elseif n==last+1 then
        close();assert(count>0,'no earlier activation comparison observed')
    end
end
