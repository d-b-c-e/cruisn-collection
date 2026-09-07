-- Read-only World 2.4 scene-level object appearance events. No guest writes.
-- Flush on page-control run boundaries, not quad-count or frame thresholds.
-- Empty/HUD-only runs do not advance the 3D scene history. Events describe
-- submitted geometry, not visibility: nearer objects can cover a new model.
-- "model_change" can be reuse of an object slot, not an LOD swap. The shared
-- fast/slow paths can also draw HUD geometry; unmatched_3d_quads reports path
-- calls without a same-frame far-gate owner, not a guaranteed missing 3D object.
local cpu=manager.machine.devices[':maincpu']; local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24','World 2.4 scene events only')
local first=tonumber(os.getenv('CRUISN_EVENTS_FIRST') or '1600')
local last=tonumber(os.getenv('CRUISN_EVENTS_LAST') or '8770')
assert(first and last and first%1==0 and last%1==0 and first>=1
    and last>=first and last-first<=9000,'invalid scene event interval')
local frame,page,scene=0,0,0
local pending,taps,admitted,seen,history,current={},{},{},{},{},{}
local events,counts=nil,nil
local scene_first,scene_last,unmatched=0,0,0
local complete_run=false
local function signed(v,bits)
    return v>=2^(bits-1) and v-2^bits or v
end
local function flush()
    if not next(current) and unmatched==0 then return end
    scene=scene+1
    local ids={};for id in pairs(current) do table.insert(ids,id) end;table.sort(ids)
    local total=0
    for _,id in ipairs(ids) do
        local v=current[id];local old=history[id]
        local missing=old and scene-old.scene-1 or -1
        total=total+v.quads
        if not old or missing>0 or old.model~=v.model then
            local reason=not old and (scene==1 and 'initial_observation' or 'first_submission')
                or old.model~=v.model and 'model_change' or 'reappeared'
            events:write(string.format('%d,%d,%d,%x,%x,%x,%d,%s,%d,%d,%d,%d,%d,%d,%d,%x,%d,%d,%d\n',
                scene,scene_first,scene_last,id,v.model,old and old.model or 0,missing,reason,
                v.quads,v.x0,v.y0,v.x1,v.y1,v.depth,v.radius,v.flags,v.texture,v.palette,v.seen))
        end
        history[id]={scene=scene,model=v.model}
    end
    counts:write(string.format('%d,%d,%d,%d,%d,%d\n',scene,scene_first,scene_last,#ids,total,unmatched))
    current={};unmatched=0;scene_first=0;scene_last=0
end
local function close()
    for _,t in ipairs(taps) do t:remove() end;taps={}
    -- The trailing run has no closing page boundary: never certify it complete.
    if events then events:close();counts:close();events=nil;counts=nil end
    current={}
end
cruisn_scenery_events_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n;admitted={}
    if n==first then
        assert(s:read_u32(0xa0)==0x04a30040 and s:read_u32(0x9c)>>16==0x1529,
            'World object signature mismatch')
        local selected=s:read_u32(0x9c)&0xffff
        events=assert(io.open('scenery-events.csv','w'))
        counts=assert(io.open('scenery-scenes.csv','w'))
        events:write('scene,first_frame,last_frame,object,model,previous_model,missing_scenes,event,quads,x0,y0,x1,y1,depth_minus_radius,radius,object_flags,first_texture,first_palette,first_far_observation\n')
        counts:write('scene,first_frame,last_frame,objects,quads,unmatched_3d_quads\n')
        page=s:read_u32(0x980040)
        table.insert(taps,s:install_read_tap(0x40,0x40,'scene_event_admission',function(o,d,m)
            if cpu.state.PC.value~=0xa1 then return end
            local id=cpu.state.AR0.value;local model=s:read_u32(selected)
            local key=id..':'..model
            seen[key]=seen[key] or frame
            admitted[id]={model=model,flags=s:read_u32(id+14),
                depth=signed(cpu.state.R3.value,32),radius=signed(cpu.state.R4.value,32),seen=seen[key]}
        end))
        table.insert(taps,s:install_write_tap(0x980040,0x980040,'scene_event_page',function(o,d,m)
            if d~=page then
                if complete_run then flush()
                else current={};unmatched=0;scene_first=0;scene_last=0;complete_run=true end
                page=d
            end
        end))
        table.insert(taps,s:install_write_tap(0x600000,0x600000,'scene_event_dma',function(o,d,m)
            if #pending<16 then table.insert(pending,d&0xffff) end
        end))
        table.insert(taps,s:install_read_tap(0x980083,0x980083,'scene_event_draw',function(o,d,m)
            local pc=cpu.state.PC.value
            if #pending>=15 and (pc==0x289 or pc==0x333) then
                if scene_first==0 then scene_first=frame end
                scene_last=frame
                local id=pc==0x333 and s:read_u32(cpu.state.SP.value) or cpu.state.AR0.value
                local a=admitted[id]
                if a then
                    local v=current[id]
                    if not v then
                        v={model=a.model,flags=a.flags,depth=a.depth,radius=a.radius,seen=a.seen,
                            quads=0,x0=32767,y0=32767,x1=-32768,y1=-32768,
                            texture=pending[15],palette=pending[2]}
                        current[id]=v
                    end
                    -- This would invalidate one-object/one-model aggregation.
                    assert(v.model==a.model,'model changed within a page-control run')
                    v.quads=v.quads+1
                    for i=0,3 do
                        local x,y=signed(pending[3+2*i],16),signed(pending[4+2*i],16)
                        v.x0=math.min(v.x0,x);v.x1=math.max(v.x1,x)
                        v.y0=math.min(v.y0,y);v.y1=math.max(v.y1,y)
                    end
                else unmatched=unmatched+1 end
            end
            pending={}
        end))
    elseif n==last+1 then close();assert(scene>0,'no 3D scene events captured') end
end
