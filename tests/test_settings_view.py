"""Presentation migration and actual launcher rows, without devices or a game."""
import configparser
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import settings_view as V
from test_graphics_options import import_shell_module


class SettingsView(unittest.TestCase):
    def test_full_settings_save_is_atomic_and_failed_edit_rolls_back(self):
        shell = import_shell_module('collection')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'collection.ini'
            original = b'[collection]\nffb=0\ncustom_note=100%\n[wheelmap]\nsteer=Owner wheel|axis:0:0:pos\n[telemetry]\nforza=192.0.2.4:9876\n'
            path.write_bytes(original)
            with mock.patch.object(shell, 'CFG', str(path)):
                state = shell.load_config()
                state['ffb'] = 80
                with mock.patch.object(V.os, 'replace', side_effect=OSError('disk denied')):
                    saved, error = shell.persist_config(state)
                self.assertFalse(saved)
                self.assertIn('disk denied', error)
                self.assertEqual(state['ffb'], 0)
                self.assertEqual(path.read_bytes(), original)
                self.assertEqual(path.with_name(path.name+'.before-settings.bak').read_bytes(), original)
                state['scale'] = 3
                self.assertEqual(shell.persist_config(state), (True, ''))
                cp = configparser.ConfigParser(interpolation=None)
                cp.read(path, encoding='utf-8')
                self.assertEqual(cp['collection']['scale'], '3')
                self.assertEqual(cp['collection']['custom_note'], '100%')
                self.assertEqual(cp['wheelmap']['steer'], 'Owner wheel|axis:0:0:pos')
                self.assertEqual(cp['telemetry']['forza'], '192.0.2.4:9876')
                self.assertFalse(list(path.parent.glob('*.tmp')))

    def test_fixed_navigation_and_scrolled_row_hit_regions(self):
        self.assertEqual(V.hit_action(1280,720,1280*.20,720*.80),'close')
        self.assertEqual(V.hit_action(1280,720,1280*.75,720*.80),'stop_ffb')
        self.assertIsNone(V.hit_action(1280,720,1280*.50,720*.80))
        self.assertEqual(V.hit_page(1280,720,1280*.39,720*.36),'ffb')
        self.assertEqual(V.hit_row(1280,720,640,720*.32,14,18),0)
        self.assertEqual(V.hit_row(1280,720,640,720*.401,14,18),7)
        self.assertIsNone(V.hit_row(1280,720,640,720*.38,14,18))
        self.assertIsNone(V.hit_page(1280,720,100,720*.36))

    def test_clear_and_failed_binding_save_preserve_other_roles(self):
        shell=import_shell_module('collection')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'collection.ini'
            path.write_text('[wheelmap]\nsteer=wheel|axis:0:0:pos\nview1=wheel|btn:2\n[collection]\nffb=0\n',encoding='utf-8')
            with mock.patch.object(shell,'CFG',str(path)):
                shell.save_wheelmap({'view1':None})
                cp=configparser.ConfigParser();cp.read(path,encoding='utf-8')
                self.assertNotIn('view1',cp['wheelmap'])
                self.assertEqual(cp['wheelmap']['steer'],'wheel|axis:0:0:pos')
                saved=path.read_bytes()
                with mock.patch.object(V.os,'replace',side_effect=OSError('denied')):
                    with self.assertRaises(OSError):shell.save_wheelmap({'steer':'replacement'})
                self.assertEqual(path.read_bytes(),saved)

    def test_round_trip_changes_only_presentation_and_preserves_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'collection.ini'
            original=b'[collection]\nffb=0\nffb_spring=37\nffb_profile=owner@8\ncustom_note=100%\n[wheelmap]\nsteer=My wheel|axis:0:0:neg\n[telemetry]\nforza=192.0.2.4:9876\n'
            path.write_bytes(original)
            state=dict(V.load({}),ffb=0,ffbspring=37,bindings={'steer':'owner'},graphics={'owner':1})
            before=copy.deepcopy(state)
            V.change(state,path,'advanced','graphics')
            V.change(state,path,'simple','graphics')
            self.assertEqual(state['settings_page'],'setup')
            self.assertEqual({k:v for k,v in state.items() if not k.startswith('settings_')},
                             {k:v for k,v in before.items() if not k.startswith('settings_')})
            self.assertEqual(path.with_name(path.name+'.before-settings-view.bak').read_bytes(),original)
            cp=configparser.ConfigParser(interpolation=None);cp.read(path,encoding='utf-8')
            self.assertEqual(cp['collection']['ffb'],'0')
            self.assertEqual(cp['collection']['custom_note'],'100%')
            self.assertEqual(cp['telemetry']['forza'],'192.0.2.4:9876')
            V.change(state,path,'advanced','ffb')
            cp.read(path,encoding='utf-8');self.assertEqual(V.load(cp['collection']),dict(settings_view='advanced',settings_page='ffb'))

    def test_failed_save_and_edit_guard_leave_state_and_file_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'collection.ini';path.write_text('[collection]\nffb=0\n',encoding='utf-8')
            state=V.load({});before=copy.deepcopy(state);data=path.read_bytes()
            with mock.patch.object(V.os,'replace',side_effect=OSError('disk unavailable')):
                with self.assertRaises(OSError):V.change(state,path,'advanced','ffb')
            self.assertEqual(state,before);self.assertEqual(path.read_bytes(),data)
            self.assertEqual(list(path.parent.glob('*.tmp')),[])
            with self.assertRaisesRegex(ValueError,'Finish or cancel'):
                V.change(state,path,'advanced','ffb',editing=True)
            self.assertEqual(state,before)
            self.assertEqual(V.load({'settings_view':'corrupt','settings_page':'graphics'}),V.load({}))

    def test_actual_pages_keep_setup_and_bindings_in_simple(self):
        shell=import_shell_module('collection')
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(shell,'CFG',str(Path(tmp)/'new.ini')):
            state=shell.load_config();self.assertEqual(state['settings_view'],'simple')
            before=copy.deepcopy(state)
            def ids(page):return [row[0] for row in shell.settings_rows(page,state,False,'fixture')]
            self.assertEqual(ids('root')[1:7],list(V.CORE))
            self.assertNotIn('graphics',ids('root'));self.assertNotIn('display',ids('root'))
            self.assertTrue({'bind_steer','bind_gas','bind_brake','buttons','trans'}<=set(ids('controls')))
            self.assertTrue({'bind_view1','bind_view2','bind_view3'}<=set(ids('cameras')))
            self.assertNotIn('feel',ids('ffb'));self.assertNotIn('diag',ids('support'))
            self.assertEqual(state,before)  # Drawing must never apply defaults/tunes.
            state.update(settings_view='advanced')
            self.assertIn('graphics',ids('root'));self.assertIn('feel',ids('ffb'));self.assertIn('diag',ids('support'))
            for page in V.PAGES:
                rows=shell.settings_rows(page,state,False,'fixture')
                self.assertEqual(rows[0][0],'view')
                self.assertEqual(len(rows),len({row[0] for row in rows}))

    def test_hidden_custom_tuning_is_discoverable(self):
        shell=import_shell_module('collection')
        state=dict(settings_view='simple',ffb=0,ffbspring=30,ffbprofile='owner@1',
                   crt=False,scale=3,margin=48,bindings={},graphics={},crackfill=True)
        rows=shell.settings_rows('ffb',state,False,'fixture')
        self.assertIn('advanced_ffb',[r[0] for r in rows])
        self.assertEqual(shell.binding_label('Wheel|btn:0'),'Wheel / Button 1')
        self.assertEqual(shell.binding_label('Wheel|axis:1:0:neg'),'Wheel / Axis 2')


if __name__=='__main__':unittest.main()
