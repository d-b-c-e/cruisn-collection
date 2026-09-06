-- MUTATING, bounded World 2.4 diagnostic for verified tree billboards.
-- Preserve all original-range objects and all general projection clamps.
-- Only originally rejected instances use the safe fast vertex path and a
-- virtual reciprocal extension. Object radius bounds every vertex below far.
local cpu=manager.machine.devices[':maincpu']; local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnwld24', 'World 2.4 diagnostic only')
local first=tonumber(os.getenv('CRUISN_TREE_FIRST') or '1998')
local last=tonumber(os.getenv('CRUISN_TREE_LAST') or '2040')
local far=tonumber(os.getenv('CRUISN_TREE_FAR') or '160000')
assert(first and last and first%1==0 and last%1==0 and first>=1
    and last>=first and last-first<=1800, 'invalid bounded tree interval')
assert(far and far%16==0 and far>80000 and far<=160000, 'invalid tree distance')
local base=0xb66f
local known={[0xca57f3]=1950,[0xca5833]=1950,[0xca5863]=818,[0xca5896]=1252}
local models={}
for token in (os.getenv('CRUISN_TREE_MODELS') or 'ca57f3'):gmatch('[^,]+') do
    assert(token:match('^%x+$'), 'expected hexadecimal tree model IDs')
    local id=tonumber(token,16)
    assert(known[id], 'tree model has not been identified')
    models[id]=known[id]
end
assert(next(models), 'no tree models selected')
local taps,out,frame,active={},nil,0,nil
local gates,reads,max_read=0,0,0
local total_reads=0
local pcs={}
for _,pc in ipairs({0x1df,0x1e3,0x1ea,0x1ec,0x21c,0x21e}) do pcs[pc]=true end
local function close()
    for _,t in ipairs(taps) do t:remove() end; taps={}
    if out then out:close();out=nil end
    active=nil
end
cruisn_tree_distance_stop=emu.add_machine_stop_notifier(close)
return function(n)
    if out then
        out:write(string.format('%d,%d,%d,%d\n',frame,gates,reads,max_read))
    end
    frame=n; gates=0; reads=0; max_read=0; active=nil
    if n==first then
        assert(s:read_u32(0xa0)==0x04a30040 and s:read_u32(0xa8)==0x04a30040
            and s:read_u32(0x4d)==base and s:read_u32(0x40)==80000
            and s:read_u32(0x9c)>>16==0x1529, 'tree path signature mismatch')
        local selected=s:read_u32(0x9c)&0xffff
        local cache={}
        for i=5000,far//16 do
            local value=math.floor(512/(16*i+1)*1000000+0.5)/1000000
            local ieee=string.unpack('<I4',string.pack('<f',value))
            cache[i]=((((ieee>>23)-127)&255)<<24)|(ieee&0x7fffff)
        end
        out=assert(io.open('tree-distance.csv','w'))
        out:write('frame,extended_gates,extended_reads,maximum_index\n')
        table.insert(taps,s:install_read_tap(0x40,0x40,'tree_far',function(o,d,m)
            local pc=cpu.state.PC.value
            if pc==0xa1 then
                active=nil
                local id=cpu.state.AR0.value
                local radius=cpu.state.R4.value
                local depth=cpu.state.R3.value
                if models[s:read_u32(selected)]==radius and s:read_u32(id+14)&0x7fffffff==0x1008
                    and depth>80000 and depth<0x80000000 then
                    assert(d==80000,'tree far limit changed during experiment')
                    if depth<=far-2*radius-16 then active=id end
                    gates=gates+1
                    return far-2*radius-16
                end
            end
            if not active or cpu.state.AR0.value~=active or pc~=0xa9 then return end
            assert(d==80000,'tree far limit changed during experiment')
            gates=gates+1
            return far
        end))
        -- Observe beyond the supported range too: fail instead of accepting an
        -- unverified reciprocal read from unrelated RAM after the table.
        table.insert(taps,s:install_read_tap(base+5000,0x1ffff,'tree_reciprocal',function(o,d,m)
            local pc=cpu.state.PC.value
            if not active or cpu.state.AR0.value~=active or cpu.state.AR2.value~=base
                or not pcs[pc] then return end
            -- Do not read selected-model RAM here: it overlaps this observed
            -- address range and a nested read can re-enter the same tap.
            local index=o-base
            assert(cache[index], 'tree reciprocal outside supported extension')
            reads=reads+1; total_reads=total_reads+1; max_read=math.max(max_read,index)
            return cache[index]
        end))
    elseif n==last+1 then close(); assert(total_reads>0,'no tree projection extension observed') end
end
