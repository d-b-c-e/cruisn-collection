"""Saved switch migration and no-reset contract; no hardware."""
import configparser
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import ffb_preferences as F
import settings_view as V
from test_graphics_options import import_shell_module


class FeedbackPreferences(unittest.TestCase):
    def test_legacy_and_explicit_off(self):
        self.assertTrue(F.enabled({}))
        self.assertFalse(F.enabled({'ffb':'0'}))
        self.assertFalse(F.enabled({'ffb':'80','ffb_enabled':'0'}))
        self.assertFalse(F.enabled({'ffb_enabled':'invalid'}))
        self.assertTrue(F.enabled({'ffb':'0','ffb_enabled':'1'}))

    def test_toggle_preserves_tune_and_failed_save(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'collection.ini'
            original=b'[collection]\nffb=65\nffb_profile=owner@7\nffb_spring=13\nffb_invert=1\n[wheelmap]\nsteer=Owner|axis:0:0:pos\n'
            path.write_bytes(original)
            for on in (False,True,False):
                F.set_enabled(path,on)
                cp=configparser.ConfigParser();cp.read(path,encoding='utf-8')
                self.assertEqual(F.enabled(cp['collection']),on)
                self.assertEqual(cp['collection']['ffb'],'65')
                self.assertEqual(cp['collection']['ffb_profile'],'owner@7')
                self.assertEqual(cp['collection']['ffb_spring'],'13')
                self.assertEqual(cp['collection']['ffb_invert'],'1')
                self.assertEqual(cp['wheelmap']['steer'],'Owner|axis:0:0:pos')
            self.assertEqual(path.with_name(path.name+'.before-ffb-switch.bak').read_bytes(),original)
            saved=path.read_bytes()
            with mock.patch.object(V.os,'replace',side_effect=OSError('denied')):
                with self.assertRaises(OSError):F.set_enabled(path,True)
            self.assertEqual(path.read_bytes(),saved)
            shell=import_shell_module('collection')
            with mock.patch.object(shell,'CFG',str(path)):
                state=shell.load_config()
                self.assertFalse(state['ffb_enabled'])
                for view in ('simple','advanced'):
                    state['settings_view']=view
                    rows={r[0]:r for r in shell.settings_rows('ffb',state,False,'')}
                    self.assertEqual(rows['ffb_enabled'][2],'Off')
                    self.assertIn('65%',rows['ffb'][2])
                shell.save_config(state)
                self.assertFalse(shell.load_config()['ffb_enabled'])
