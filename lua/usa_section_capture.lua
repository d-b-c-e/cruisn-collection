-- Bounded USA section placement, final descriptor and material oracle.
-- Raw game operands stay LOCAL. Main RAM reads bypass speedup/tap handlers.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local ram=assert(manager.machine.memory.shares[':ram_base'])
local first=tonumber(os.getenv('CRUISN_USA_SECTION_FIRST') or '1800')
local last=tonumber(os.getenv('CRUISN_USA_SECTION_LAST') or '5010')
assert(first and last and first%1==0 and last%1==0 and first>=1800 and last>=first
 and last-first<=6000,'invalid USA section interval')
local frame,taps,out,busy,failure,count,pending=0,{},nil,false,nil,0,nil
local function read(p)
 if p>=0 and p<0x20000 then return ram:read_u32(p*4)end
 assert(p>=0x809800 and p<0x80a000 or p>=0xc00000 and p<0x1000000,'unmapped section operand')
 return s:read_u32(p)
end
local function words(p,n)local t={};assert(n>=0 and n<=64);for i=0,n-1 do t[#t+1]=read(p+i)end;return t end
local function emit(r)
 local parts={};for k,v in pairs(r)do parts[#parts+1]='"'..k..'":'..(type(v)=='table' and '['..table.concat(v,',')..']' or tostring(v))end;table.sort(parts)
 out:write('{'..table.concat(parts,',')..'}\n');count=count+1;assert(count<10000)
end
local function finish()
 if not pending then return end
 pending.actual=words(pending.object,34)
 pending.final_pc=cpu.state.PC.value
 emit(pending);pending=nil
end
local function guard(fn)return function(...)
 if busy or failure then return end;busy=true
 local ok,e=pcall(fn,...);busy=false;if not ok then failure=tostring(e)end
end end
local function close()
 for _,tap in ipairs(taps)do tap:remove()end;taps={}
 if out then
  out:close();out=nil
  local receipt=assert(io.open('usa-section-capture.json','w'))
  receipt:write(string.format('{"schema":1,"first":%d,"last":%d,"objects":%d,"complete":%s}\n',
   first,last,count,(not failure and not pending and frame>last) and 'true' or 'false'))
  receipt:close()
 end
end
cruisn_usa_sections_stop=emu.add_machine_stop_notifier(close)
return function(n)
 frame=n;assert(not failure,failure)
 if n==first then
  assert(read(0x40b9)==0x62007035 and read(0x4114)==0x0840040f and read(0x95f7)==0x6200b072)
  out=assert(io.open('usa-sections.jsonl','w'));out:setvbuf('full',65536)
  -- Next allocation starts after the prior class handling. The stage read
  -- completes the last object of each list. Neither callback executes guest code.
  taps[#taps+1]=s:install_read_tap(0xc9b3,0xc9b3,'usa_section_next',guard(function()
   if cpu.state.PC.value==0x7052 then finish()end
  end))
  taps[#taps+1]=s:install_read_tap(0xe4ab,0xe4ab,'usa_section_end',guard(function()
   if cpu.state.PC.value==0x414f then finish()end
  end))
  taps[#taps+1]=s:install_read_tap(0x10585,0x1979c,'usa_section_ready',guard(function(p)
   if (p-0x10585)%34~=15 or cpu.state.PC.value~=0x4115 then return end
   assert(not pending,'unfinalized USA allocation')
    local object=cpu.state.AR4.value;assert(p==object+15)
    local section=cpu.state.AR7.value;local source=cpu.state.AR5.value-6
    local def=words(source,6);local prefix=read(def[1]-1);local base=read(0x9ea9)
    pending={frame=frame,serial=count+1,object=object,source=source,section_pointer=section,
      definition=def,section_words=words(section,12),section_flags=read(0xe4aa),stage=read(0xe4ab),
      heading=read(0xe4ac),matrix=words(read(0x5a),9),trig_constants=words(0xc8ed,7),
      ready=words(object,34),model_prefix=prefix,palette_base=base,palette_binding=read(base+(prefix&0xfff)),
      camera=words(read(0x45),3),view=words(read(0x47),9)}
  end))
 elseif n==last+1 then assert(not pending,'incomplete final USA allocation');close();assert(count>0,'empty USA section probe')end
end
