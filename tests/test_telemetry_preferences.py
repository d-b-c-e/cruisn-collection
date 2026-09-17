"""No sockets: telemetry validation, atomic persistence and real launcher wiring."""
import configparser
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import telemetry_preferences as T
import settings_view
from test_graphics_options import import_shell_module


class TelemetryPreferences(unittest.TestCase):
    def test_native_destination_bounds(self):
        self.assertEqual(T.destination('on',forza=True),T.PRESET)
        self.assertEqual(T.destination('20777',forza=False),'127.0.0.1:20777')
        self.assertEqual(T.destination('localhost:5300,192.0.2.5:1234',forza=True),'127.0.0.1:5300,192.0.2.5:1234')
        for value in ('host.example:5300','::1:5300','127.0.0.1:0','127.0.0.1:65536','127.0.0.1:-1','127.0.0.1:abc',','.join(['127.0.0.1:5300']*5)):
            with self.subTest(value=value),self.assertRaises(ValueError):T.destination(value,forza=True)
        with self.assertRaises(ValueError):T.destination('127.0.0.1:1,127.0.0.1:2',forza=False)

    def test_off_retains_custom_destinations_and_other_preferences(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'collection.ini'
            path.write_text('[collection]\nffb=0\n[telemetry]\nforza=192.0.2.4:9876\nudp=127.0.0.1:20777\ncustom=keep\n',encoding='utf-8')
            cp=configparser.ConfigParser(interpolation=None);cp.read(path,encoding='utf-8')
            self.assertTrue(T.enabled(cp['telemetry']))
            T.set_enabled(path,cp['telemetry'],False)
            cp.read(path,encoding='utf-8')
            self.assertFalse(T.enabled(cp['telemetry']))
            self.assertEqual(T.launch_overrides(cp['telemetry'],{}),{})
            self.assertEqual(cp['telemetry']['forza'],'192.0.2.4:9876')
            T.set_enabled(path,cp['telemetry'],True);cp.read(path,encoding='utf-8')
            self.assertEqual(T.launch_overrides(cp['telemetry'],{}),dict(MIDV_TELEM_FORZA='192.0.2.4:9876',MIDV_TELEM_UDP='127.0.0.1:20777'))
            self.assertEqual(T.launch_overrides(cp['telemetry'],dict(MIDV_TELEM_FORZA='explicit')),dict(MIDV_TELEM_UDP='127.0.0.1:20777'))
            self.assertEqual(cp['collection']['ffb'],'0');self.assertEqual(cp['telemetry']['custom'],'keep')

    def test_atomic_connection_and_failed_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'collection.ini';path.write_text('[telemetry]\nenabled=0\nforza=on\n',encoding='utf-8')
            original=path.read_bytes()
            with self.assertRaises(ValueError):T.apply_connection(path,T.PRESET,'invalid')
            self.assertEqual(path.read_bytes(),original)
            with mock.patch.object(settings_view.os,'replace',side_effect=OSError('denied')):
                with self.assertRaises(OSError):T.apply_connection(path,'192.0.2.8:5300','')
            self.assertEqual(path.read_bytes(),original)
            T.apply_connection(path,'192.0.2.8:5300','');cp=configparser.ConfigParser();cp.read(path,encoding='utf-8')
            self.assertFalse(T.enabled(cp['telemetry']))
            self.assertEqual(cp['telemetry']['forza'],'192.0.2.8:5300')

    def test_first_enable_and_actual_simple_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'collection.ini';T.set_enabled(path,{},True)
            cp=configparser.ConfigParser();cp.read(path,encoding='utf-8')
            self.assertEqual(T.launch_overrides(cp['telemetry'],{}),dict(MIDV_TELEM_FORZA=T.PRESET))
            shell=import_shell_module('collection')
            with mock.patch.object(shell,'CFG',str(path)):
                state=shell.load_config();rows=shell.settings_rows('telemetry',state,False,'')
                ids=[r[0] for r in rows]
                self.assertIn('telemetry_enabled',ids);self.assertIn('advanced_telemetry',ids)
                state['settings_view']='advanced'
                self.assertIn('connection',[r[0] for r in shell.settings_rows('telemetry',state,False,'')])

    def test_keeper_off_never_opens_a_socket(self):
        shell=import_shell_module('collection')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'collection.ini';path.write_text('[telemetry]\nenabled=0\nforza=192.0.2.8:5300\n',encoding='utf-8')
            with mock.patch.object(shell,'CFG',str(path)),mock.patch('socket.socket',side_effect=AssertionError('socket opened')):
                keeper=shell.ForzaKeeper()
                self.assertEqual(keeper.targets,())
                self.assertIsNone(keeper._sock)


if __name__=='__main__':unittest.main()
