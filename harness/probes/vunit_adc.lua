-- Read-only ADC command/control/consumer journal. Never reads the ADC itself.
local cpu=manager.machine.devices[':maincpu'];local s=cpu.spaces.program
local rom=manager.machine.system.name
assert(rom=='crusnusa' or rom=='crusnwld24' or rom=='offroadc','unsupported V-Unit ADC game')
assert(os.getenv('MIDV_FFB')=='0','ADC diagnostics require physical FFB off')
local last=assert(tonumber(os.getenv('CRUISN_VUNIT_ADC_LAST')))
assert(last>=2 and last<=20000 and last==math.floor(last),'ADC frame bound')
local frame=0;local taps={};local out;local rows=0;local counts={C=0,W=0,R=0}
local failed;local complete=false;local first_time;local last_time
local function close()
 for _,tap in ipairs(taps) do tap:remove() end;taps={}
 if not out then return end
 out:close();out=nil
 local f=assert(io.open('vunit-adc-receipt.json','w'))
 f:write(string.format('{"schema":1,"game":%q,"first":1,"last":%d,"first_seconds":%.12f,"last_seconds":%.12f,"complete":%s,"rows":%d,"control":%d,"writes":%d,"reads":%d,"error":%s}\n',rom,last,first_time,last_time or emu.time(),tostring(complete and not failed),rows,counts.C,counts.W,counts.R,failed and string.format('%q',failed) or 'null'));f:close()
end
cruisn_vunit_adc_stop=emu.add_machine_stop_notifier(close)
local function observe(kind)
 return function(offset,data,mask)
  if failed then return end
  local ok,err=pcall(function()
   rows=rows+1;assert(rows<=196608,'ADC event budget')
   counts[kind]=counts[kind]+1
   out:write(string.format('%d,%s,%d,%.12f,%x,%x,%x\n',rows,kind,frame,emu.time(),cpu.state.PC.value,data,mask))
  end)
  if not ok then failed=tostring(err) end
 end
end
return function(n)
 frame=n;assert(not failed,failed)
 if n==1 then
  first_time=emu.time();out=assert(io.open('vunit-adc.csv','w'));out:setvbuf('full',65536)
  out:write('sequence,kind,frame,seconds,pc,data,mask\n')
  taps[#taps+1]=s:install_write_tap(0x994000,0x994000,'ffb_adc_control',observe('C'))
  taps[#taps+1]=s:install_write_tap(0x993000,0x993000,'ffb_adc_command',observe('W'))
  taps[#taps+1]=s:install_read_tap(0x993000,0x993000,'ffb_adc_consumer',observe('R'))
 end
 if n==last then last_time=emu.time();complete=true;close() end
end
