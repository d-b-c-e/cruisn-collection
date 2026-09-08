-- Exotica2.4 global loader/admission observation. Read-only unless explicitly opted in.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
assert(manager.machine.system.name=='crusnexo','Exotica2.4 only')
local first=tonumber(os.getenv('CRUISN_EXOTICA_STREAM_FIRST') or '2500')
local last=tonumber(os.getenv('CRUISN_EXOTICA_STREAM_LAST') or '5990')
local admission=tonumber(os.getenv('CRUISN_EXOTICA_ADMISSION') or '0')
assert(first and last and first%1==0 and last%1==0 and first>=1 and last>first and last-first<=12000)
assert(admission==0 or admission==160000 or admission==190000,'unsupported bounded admission trial')
local frame,sequence,failed,out=0,0,nil,nil
local taps={}
local function signed(v) return v>=0x80000000 and v-0x100000000 or v end
local function close()
 for _,t in ipairs(taps) do t:remove() end;taps={}
 if out then out:close();out=nil end
end
cruisn_exotica_streaming_stop=emu.add_machine_stop_notifier(close)
local function tap(a,b,name,fn)
 taps[#taps+1]=s:install_read_tap(a,b,name,function(o,d)
  if failed or frame>last then return end
  local ok,result=pcall(fn,o,d)
  if not ok then failed=tostring(result);return end
  return result -- nil except the explicit admission trial's guarded two consumers.
 end)
end
local function row(kind,pc,object,model,flags,depth,threshold,cursor,pointer)
 sequence=sequence+1;assert(sequence<=1000000,'streaming probe budget exceeded')
 assert(out:write(string.format('%d,%d,%s,%x,%x,%x,%x,%d,%d,%d,%x,%d,%d,%d,%d,%d\n',
  frame,sequence,kind,pc,object,model,flags,depth,threshold,cursor,pointer,
  s:read_u32(0x10c0),s:read_u32(0x591),s:read_u32(0x592),s:read_u32(0x594),
  (kind=='admission' or kind=='admission_check') and (admission~=0 and admission or threshold) or threshold)))
end
return function(n)
 frame=n;assert(not failed,failed)
 if n==first then
  for _,w in ipairs({{0xb710,0x08607530},{0xb711,0x0ae00003},{0xb712,0x15200589},
   {0xb720,0x02210591},{0xb721,0x15210594},{0xb771,0x15400014},
   {0xb772,0x04a00589},{0xb773,0x6a0a0014},{0xb774,0x08400014},{0xb775,0x04a00589},
   {0xb7b9,0x08200594},{0xb7ba,0x0260000c},{0xb7bb,0x04a00598},{0xb7bc,0x6a07ff57},
   {0xb7bd,0x6200b7e8},{0xb7e8,0x082e0597},{0xb81a,0x15270598}}) do
   assert(s:read_u32(w[1])==w[2],string.format('streaming profile mismatch at%x',w[1]))
  end
  out=assert(io.open('exotica-streaming.csv','w'));out:setvbuf('full',65536)
  out:write('frame,sequence,kind,pc,object,model,flags,depth,threshold,cursor,pointer,section,lead,tail,upper,effective_threshold\n')
  tap(0x589,0x589,'exotica_pending_depth',function(o,d)
   local pc=cpu.state.PC.value
   if pc~=0xb773 and pc~=0xb776 then return end
   local object=cpu.state.AR0.value
   assert(object>=0x1000 and object+0x1d<0x40000,'pending object outside RAM')
   local depth=signed(cpu.state.R0.value)
   assert(signed(s:read_u32(object+0x14))==depth,'pending depth operand mismatch')
   row(pc==0xb773 and 'admission' or 'admission_check',pc,object,s:read_u32(object+0x11),
    s:read_u32(object+0xf),depth,signed(d),0,0)
   if admission~=0 then return admission end
  end)
  tap(0x598,0x598,'exotica_loader_lookahead',function(o,d)
   if cpu.state.PC.value~=0xb7bc then return end
   local threshold=signed(cpu.state.R0.value)
   assert(threshold==signed(s:read_u32(0x594))+12,'loader threshold changed')
   row('lookahead',0xb7bc,0,0,0,0,threshold,signed(d),0)
  end)
  tap(0x597,0x597,'exotica_loader_entry',function(o,d)
   if cpu.state.PC.value==0xb7e9 then row('load',0xb7e9,0,0,0,0,0,0,d) end
  end)
 elseif n==last+1 then close();assert(sequence>0,'no streaming observations') end
end
