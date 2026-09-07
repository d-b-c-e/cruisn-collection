"""Exercise release defaults and generated controls without launching a game.

These checks prove configuration behavior, not physical shifting or wheel feel.
All writes and device-layout substitutions are confined to a temporary rig.
"""
import configparser
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'harness'))
ROMS = ('crusnusa', 'crusnwld24', 'crusnwld', 'offroadc', 'crusnexo')
# Independently pinned operator-setting addresses, including every USA mirror.
FREEPLAY = {'crusnusa': ('nvram', (0x190,0x195,0x19a,0x19f)),
            'crusnwld24': ('nvram', (0x1ac,)), 'crusnwld': ('nvram', (0x1ac,)),
            'offroadc': ('nvram', (0x1cc,)), 'crusnexo': ('m48t35', (0x73,))}


class ReleaseFixturesTests(unittest.TestCase):
    def test_offroad_edits_keep_the_boot_checksum_and_unrelated_bytes(self):
        from cmos_settings import offroad_checksum, set_bytes
        source = (ROOT/'fixtures/nvram-offroadc/nvram').read_bytes()
        self.assertEqual(offroad_checksum(source), (0xc2ad78, 0xc2ad78))
        off = set_bytes(source, 'offroadc', 'nvram', [0x1cc], 0)
        self.assertEqual(offroad_checksum(off), (0xc2ad77, 0xc2ad77))
        self.assertEqual([i for i,(a,b) in enumerate(zip(source,off)) if a!=b], [0x1cc,0x35c])
        self.assertEqual(set_bytes(off, 'offroadc', 'nvram', [0x1cc], 1), source)
        # A settings layout from another revision is not guessed or modified.
        bad = bytearray(source); bad[0x37c] = 0
        with self.assertRaises(ValueError): set_bytes(bad, 'offroadc', 'nvram', [0x1cc], 1)
        volume = set_bytes(source, 'offroadc', 'nvram', [0x2fc], 42)
        self.assertEqual([i for i,(a,b) in enumerate(zip(source,volume)) if a!=b], [0x2fc])

    def test_every_fresh_seed_has_free_play_enabled(self):
        for rom, (filename, addresses) in FREEPLAY.items():
            with self.subTest(rom=rom):
                data = (ROOT/'fixtures'/f'nvram-{rom}'/filename).read_bytes()
                self.assertEqual([data[a] for a in addresses], [1]*len(addresses))
                if rom == 'offroadc':
                    from cmos_settings import offroad_checksum
                    expected, stored = offroad_checksum(data)
                    self.assertEqual(expected, stored)


@unittest.skipUnless(sys.platform == 'win32', 'actual launcher configuration uses Windows APIs')
class ReleaseLauncherTests(unittest.TestCase):
    def setUp(self):
        missing = importlib.util.find_spec('moderngl') is None
        if missing: sys.modules['moderngl'] = types.ModuleType('moderngl')
        try:
            import collection
            import run_rig
        finally:
            if missing: sys.modules.pop('moderngl',None)
        self.shell, self.rig = collection, run_rig
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        self.cfg = self.root/'rig/collection.ini'
        shutil.copytree(ROOT/'fixtures', self.root/'fixtures')
        for obj, name, value in ((collection,'POC',str(self.root)), (collection,'CFG',str(self.cfg)),
                                 (run_rig,'POC',str(self.root)), (run_rig,'CTRLR_SRC',str(self.root/'absent.cfg'))):
            patcher = mock.patch.object(obj, name, value)
            patcher.start(); self.addCleanup(patcher.stop)
        patcher = mock.patch.object(run_rig,'axis_layout',return_value={})
        patcher.start(); self.addCleanup(patcher.stop)

    def write_config(self, collection=None, bindings=None):
        cp = configparser.ConfigParser()
        cp['collection'] = collection or {}
        cp['wheelmap'] = bindings or {}
        self.cfg.parent.mkdir(parents=True,exist_ok=True)
        with self.cfg.open('w') as out: cp.write(out)

    def test_fresh_defaults_and_saved_choices_survive(self):
        state = self.shell.load_config()
        self.assertTrue(state['crt'])
        self.assertIsNone(state['margin'])  # full 16:9
        self.assertEqual(state['world_rom'], 'crusnwld24')
        self.assertEqual((state['ffb'],state['ffbprofile']), (50,'cruisn-vunit@2'))
        self.assertFalse(any(v for game in state['graphics'].values() for v in game.values()))
        self.write_config({'crt':'0','margin':'0','transmission':'sequential','ffb':'35','custom':'keep'},
                          {'shiftup':'Wheel|btn:5','shiftdn':'Wheel|btn:6'})
        state = self.shell.load_config()
        self.shell.save_config(state)
        self.assertFalse(self.shell.load_config()['crt'])
        self.assertEqual(self.shell.load_config()['margin'],0)
        cp = configparser.ConfigParser(); cp.read(self.cfg)
        self.assertEqual(cp['collection']['custom'],'keep')
        self.assertEqual(cp['wheelmap']['shiftup'],'Wheel|btn:5')

    def test_first_boot_seeds_but_never_overwrites_existing_nvram(self):
        for rom in ROMS:
            self.rig.prepare_rig(rom, crt=True, zeus_gl=rom=='crusnexo')
            filename, addresses = FREEPLAY[rom]
            path = self.root/'rig/nvram'/rom/filename
            data = bytearray(path.read_bytes())
            self.assertTrue(all(data[a]==1 for a in addresses))
            data[addresses[0]] = 0
            path.write_bytes(data)
            self.rig.prepare_rig(rom, crt=True, zeus_gl=rom=='crusnexo')
            self.assertEqual(path.read_bytes(),data)

    def test_shifter_mode_and_cabinet_configuration_for_every_game(self):
        for mode in ('hpattern','sequential'):
            keys = ('gear1','gear2','gear3','gear4') if mode=='hpattern' else ('shiftup','shiftdn')
            self.write_config({'transmission':mode}, {k:f'Wheel|btn:{i}' for i,k in enumerate(keys)})
            for rom in ROMS:
                rig,_ = self.rig.prepare_rig(rom)
                self.rig.apply_shifter_config(rig,rom)
                ports = ET.parse(Path(rig)/'cfg'/f'{rom}.cfg').findall('.//port')
                values = {(p.get('tag'),int(p.get('mask'))):int(p.get('value')) for p in ports}
                if rom!='crusnexo': self.assertEqual(values[(':CONF',7)],0 if mode=='hpattern' else 5)
                if rom.startswith('crusnwld'): self.assertEqual(values[(':DSW',0x20)],0)
                if rom=='crusnexo': self.assertEqual(values[(':DIPS',0x400)],0)

    def test_offroad_freeplay_toggle_updates_checksum_and_preserves_other_settings(self):
        from cmos_settings import offroad_checksum
        self.rig.prepare_rig('offroadc')
        path = self.root/'rig/nvram/offroadc/nvram'
        before = path.read_bytes()
        for enabled in (0,1):
            self.assertTrue(self.shell.cmos_write('offroadc','nvram',[0x1cc],enabled))
            data = path.read_bytes()
            self.assertEqual(data[0x1cc], enabled)
            expected,stored = offroad_checksum(data)
            self.assertEqual(expected,stored)
        self.assertEqual(path.read_bytes(),before)

    def test_rebinding_replaces_old_button_and_keeps_other_mode_and_keyboard(self):
        self.write_config({'transmission':'sequential'}, {'gear1':'Wheel|btn:1','shiftup':'Wheel|btn:32',
            'shiftdn':'Wheel|btn:33','start':'Wheel|btn:4'})
        self.shell.save_wheelmap({'shiftup':'Wheel|btn:35','start':'Wheel|btn:7'})
        cp=configparser.ConfigParser(); cp.read(self.cfg)
        self.assertEqual(cp['wheelmap']['gear1'],'Wheel|btn:1')
        rig,_=self.rig.prepare_rig('crusnwld24')
        self.rig.sanitized_ctrlrpath(rig,'crusnwld24')
        tree=ET.parse(Path(rig)/'ctrlr/EmuEzRacing.cfg')
        def seq(system,port):
            return tree.find(f".//system[@name='{system}']/input/port[@type='{port}']/newseq").text
        self.assertEqual(seq('default','START1'),'KEYCODE_1 OR JOYCODE_1_BUTTON8')
        self.assertIn('ADDSW4',seq('default','P1_BUTTON6'))
        self.assertIn('ADDSW4',seq('crusnexo','P1_BUTTON11'))
        self.assertNotIn('JOYCODE_1_ADDSW1',ET.tostring(tree.getroot()).decode())
        self.assertEqual(seq('default','UI_CANCEL'),'KEYCODE_F12')
