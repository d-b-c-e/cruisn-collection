-- MUTATING, bounded World 2.4 diagnostic: admit selected scenery earlier.
-- Only override the whole-object far rejection. Leave the original far/near
-- fast-path decision and reciprocal clamps intact, preserving submitted size.
-- This intentionally preserves the game's far-clamped perspective for these
-- models. It is not a general-purpose correct-perspective distance extension.
local cpu=manager.machine.devices[':maincpu']; local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24', 'World 2.4 diagnostic only')
local first=tonumber(os.getenv('CRUISN_SCENERY_FIRST') or '1800')
local last=tonumber(os.getenv('CRUISN_SCENERY_LAST') or '2200')
local limit=tonumber(os.getenv('CRUISN_SCENERY_LIMIT') or '160000')
local models={}; local total=0
for token in (os.getenv('CRUISN_SCENERY_MODELS') or 'cb1a8b'):gmatch('[^,]+') do
    assert(token:match('^%x+$'), 'expected comma-separated hexadecimal model addresses')
    local id=tonumber(token,16)
    assert(id>=0xc00000 and id<=0xffffff, 'model must be in World ROM')
    models[id]=true; total=total+1
end
assert(total>0 and total<=32 and first and last and first%1==0 and last%1==0
    and first>=1 and last>=first and last-first<=1800 and limit and limit%1==0
    and limit>80000 and limit<=320000, 'invalid bounded scenery experiment')
local tap,out,frame=nil,nil,0
local function close()
    if tap then tap:remove();tap=nil end
    if out then out:close();out=nil end
end
cruisn_scenery_admission_stop=emu.add_machine_stop_notifier(close)
return function(n)
    frame=n
    if n==first then
        assert(s:read_u32(0xa0)==0x04a30040 and s:read_u32(0xa8)==0x04a30040
            and s:read_u32(0x40)==80000 and s:read_u32(0x9c)>>16==0x1529,
            'World far-path signature mismatch')
        local selected=s:read_u32(0x9c)&0xffff
        out=assert(io.open('scenery-admission.csv','w'))
        out:write('frame,object,model,original_limit,effective_limit\n')
        tap=s:install_read_tap(0x40,0x40,'selected_scenery_far',function(o,d,m)
            if cpu.state.PC.value~=0xa1 then return end
            local model=s:read_u32(selected)
            if not models[model] then return end
            assert(d==80000,'far limit changed during experiment')
            out:write(string.format('%d,%x,%x,%d,%d\n',frame,cpu.state.AR0.value,model,d,limit))
            return limit
        end)
    elseif n==last+1 then close() end
end
