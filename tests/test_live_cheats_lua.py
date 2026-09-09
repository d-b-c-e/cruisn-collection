"""Execute the shipped Lua loader with a mocked native command boundary.

These check frame scheduling, one-shot journaling and replay, not cheat-address
correctness. Actual MAME interpreter/game checks are separate diagnostics.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from lupa.lua54 import LuaError, LuaRuntime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import cheats

ROOT = Path(__file__).resolve().parents[1]
XML = b'''<mamecheat version="1">
<cheat desc="Timer"><script state="run"/></cheat>
<cheat desc="Finish"><script state="on"/></cheat>
<cheat desc="Restore code"><script state="on"/><script state="off"/></cheat>
<cheat desc="Nitro"><parameter><item value="1">One</item><item value="2">Two</item></parameter><script state="change"/></cheat>
</mamecheat>'''

MOCK = '''
os.getenv = function(name)
    if name == 'MIDV_CHEATS' then return directory end
    if name == 'SNAP_SESSION_LOG' then return 'fixture' end
end
commands, queued, publications = {}, {}, {}
local entries = {
 {index=1,description='Timer',kind='toggle',state='Off',comment=''},
 {index=2,description='Finish',kind='oneshot',state='Set',comment=''},
 {index=3,description='Restore code',kind='toggle',state='Off',comment=''},
 {index=4,description='Nitro',kind='oneshot_parameter',state='Set',comment=''},
}
emu = {romname=function() return 'crusnusa' end,
       register_stop=function(fn) stop=fn end}
manager = {}
function manager:cheat_entries() return entries end
function manager:cheat_menu_take() local result=queued; queued={}; return result end
function manager:cheat_menu_publish(rows, readonly)
 publications[#publications+1]={rows=rows,readonly=readonly}
end
function manager:cheat_command(index, description, action)
 assert(entries[index].description==description)
 commands[#commands+1]={index=index,action=action}
 local e=entries[index]
 if action=='off' then e.state='Off'; e.position=0
 elseif action=='next' then
   e.position=(e.position or 0)+1
   e.state=index==4 and ({'One','Two'})[e.position] or 'On'
 elseif action=='previous' then
   e.position=e.position-1
   e.state=index==4 and ({'Off','One','Two'})[e.position+1] or 'Off'
 end
 return true
end
'''


class LiveCheatLuaTests(unittest.TestCase):
    def bundle(self, path):
        (path/'cheats').mkdir(parents=True)
        (path/'cheats/crusnusa.xml').write_bytes(XML)
        return cheats.prepare(ROOT, path, 'crusnusa')

    def vm(self, directory):
        vm = LuaRuntime(unpack_returned_tuples=True)
        vm.globals().directory = str(directory)
        vm.execute(MOCK)
        tick = vm.execute((directory/'cheats.lua').read_text(encoding='utf-8'))
        return vm, tick

    def test_live_actions_replay_at_exact_frames_including_repeated_one_shots(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); record=self.bundle(root/'record'); replay=self.bundle(root/'replay')
            vm,tick=self.vm(record)
            tick()
            self.assertEqual(len(vm.globals().commands),0) # All off at boot.
            vm.execute('queued={{index=1,steps=1,activate=false},{index=3,steps=1,activate=false}}')
            self.assertEqual(len(vm.globals().commands),0) # Menu only stages requests.
            tick()
            vm.execute('queued={{index=2,steps=0,activate=true},{index=2,steps=0,activate=true},'
                       '{index=4,steps=2,activate=true},{index=3,steps=0,activate=false}}')
            tick(); tick(); vm.globals().stop()
            expected=(record/'actions.csv').read_bytes()
            self.assertEqual(expected.count(b'3,2,0,1'),2)
            self.assertIn(b'3,3,0,0',expected) # Restore code is switched off at frame 3.
            (replay/'replay-actions.csv').write_bytes(expected)
            other,replay_tick=self.vm(replay)
            other.execute('queued={{index=1,steps=0,activate=false}}') # Ignored during replay.
            for _ in range(4): replay_tick()
            self.assertTrue(other.globals().publications[1]['readonly'])
            other.globals().stop()
            for name in ('actions.csv','events.csv'):
                self.assertEqual((record/name).read_bytes(),(replay/name).read_bytes())
            def commands(runtime):
                return [(runtime.globals().commands[i]['index'], runtime.globals().commands[i]['action'])
                        for i in range(1,len(runtime.globals().commands)+1)]
            self.assertEqual(commands(vm),commands(other))
            self.assertEqual(commands(vm).count((2,'activate')),2)
            self.assertIn((3,'off'),commands(vm))

    def test_replay_rejects_bad_order_bad_selection_and_unconsumed_actions(self):
        with tempfile.TemporaryDirectory() as td:
            bundle=self.bundle(Path(td))
            for rows in ('2,1,1,0\n1,1,0,0\n','2,99,1,0\n','2,1,99,0\n','bad\n'):
                (bundle/'replay-actions.csv').write_text('frame,index,steps,activate\n'+rows,encoding='utf-8')
                with self.assertRaises(LuaError): self.vm(bundle)
            (bundle/'replay-actions.csv').write_text('frame,index,steps,activate\n3,2,0,1\n',encoding='utf-8')
            vm,tick=self.vm(bundle); tick()
            with self.assertRaisesRegex(LuaError,'before recorded cheat actions'): vm.globals().stop()

    def test_older_native_build_can_launch_and_replay_while_live_menu_is_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            bundle=self.bundle(Path(td))
            (bundle/'replay-actions.csv').write_text('frame,index,steps,activate\n2,2,0,1\n',encoding='utf-8')
            vm=LuaRuntime(unpack_returned_tuples=True);vm.globals().directory=str(bundle)
            vm.execute(MOCK)
            vm.execute('manager.cheat_menu_publish=nil; manager.cheat_menu_take=nil')
            tick=vm.execute((bundle/'cheats.lua').read_text(encoding='utf-8'))
            tick();tick();vm.globals().stop()
            self.assertEqual(len(vm.globals().commands),1)
            self.assertEqual(vm.globals().commands[1]['action'],'activate')
            self.assertIn('2,2,0,1', (bundle/'actions.csv').read_text(encoding='utf-8'))

    def test_live_activation_rejects_catalog_drift_and_out_of_range_values(self):
        with tempfile.TemporaryDirectory() as td:
            bundle=self.bundle(Path(td)); vm,tick=self.vm(bundle); tick()
            vm.execute('queued={{index=1,steps=99,activate=false}}')
            with self.assertRaisesRegex(LuaError,'Invalid live cheat value'): tick()
            vm.globals().stop()
            settings=(bundle/'settings.lua').read_text(encoding='utf-8')
            (bundle/'settings.lua').write_text(settings.replace('rom='+cheats.lua_string('crusnusa'),
                'rom='+cheats.lua_string('crusnexo')),encoding='utf-8')
            with self.assertRaisesRegex(LuaError,'another ROM revision'): self.vm(bundle)
