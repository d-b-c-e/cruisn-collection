from pathlib import Path
from types import SimpleNamespace
import csv
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from vunit_bootstrap import configure, verify


class BootstrapTests(unittest.TestCase):
    def test_explicit_scope(self):
        args = SimpleNamespace(candidate='x', vunit_bootstrap='scenes', usa_host_scenery='draw')
        settings = dict(MIDV_GL='1', MIDV_FFB='0', MIDV_USA_HOST_SCENERY='2',
                        MIDV_USA_HOST_FUTURE='1', MIDV_USA_HOST_LAYER='3',
                        MIDV_USA_HOST_FIRST='3500', MIDV_USA_HOST_LAST='5000')
        self.assertEqual(configure(args, 'crusnusa', settings, 5012)['last'], 5000)
        for rom in ('crusnwld', 'crusnwld24', 'offroadc', 'crusnexo'):
            with self.assertRaises(ValueError):
                configure(args, rom, settings.copy(), 5012)
        for change in ({'candidate': None}, {'headless': True}, {'native_renderer': True},
                       {'usa_host_scenery': None}, {'vunit_bootstrap': None}):
            with self.assertRaises(ValueError):
                configure(SimpleNamespace(**(vars(args) | change)), 'crusnusa', settings.copy(), 5012)
        for key, value in [('MIDV_FFB', '1'), ('MIDV_GL', '0'), ('MIDV_USA_HOST_FUTURE', '0'),
                           ('MIDV_USA_HOST_LAYER', '2'), ('MIDV_USA_HOST_LAST', '5011')]:
            with self.assertRaises(ValueError):
                configure(args, 'crusnusa', settings | {key:value}, 5012)
        self.assertIsNone(configure(SimpleNamespace(), 'crusnusa', {}, 5012))

    def test_each_game_requires_its_own_mode_and_receipt(self):
        from vunit_bootstrap import PROFILES
        for rom, (game, pc, address) in PROFILES.items():
            args = SimpleNamespace(candidate='x', vunit_bootstrap='scenes', **{game+'_host_scenery':'draw'})
            prefix='MIDV_'+game.upper()+'_HOST_'
            settings={'MIDV_GL':'1','MIDV_FFB':'0',**{prefix+k:v for k,v in
                      [('SCENERY','2'),('FUTURE','1'),('LAYER','3'),('FIRST','1800'),('LAST','1900')]}}
            trial=configure(args,rom,settings,1902)
            self.assertEqual(trial['rom'],rom)
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary)
                (root/'stdout.log').write_text('VUNIT_BOOTSTRAP scenes=1 first=actual last=1900\n')
                # A different game's boundary must fail before any files can qualify.
                (root/'stderr.log').write_text(f'VUNIT_BOOTSTRAP_READY frame=1800 pc={pc^1:x} address={address:x}\n')
                with self.assertRaisesRegex(ValueError,'activation'):
                    verify(trial,root)

    def test_activation_and_truncated_evidence(self):
        from analyze_usa_host import COUNTERS, PHASES
        trial = dict(mode='scenes', rom='crusnusa', capture_reference_first=3500, last=5000)
        ack = 'VUNIT_BOOTSTRAP scenes=1 first=actual last=5000\n'
        ready = 'VUNIT_BOOTSTRAP_READY frame=739 pc=81 address=40\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'stdout.log').write_text(ack)
            (root/'stderr.log').write_text(ready)
            for name, size in [('ram',0x80000), ('fast',0x2000)]:
                (root/f'vunit-bootstrap-{name}.bin').write_bytes(bytes(size))
            row = {n:'0' for n in (*COUNTERS, *PHASES, 'microseconds',
                   'future_start','future_loading','future_number','future_sections','future_definitions',
                   'future_special','future_unbound','future_deferred','future_ready','future_uploads',
                   'future_partial','future_new_sections')}
            row.update(frame='739', time='12.3', page='0', mode='2', host_far='240000',
                       quads_hash='14650fb0739d0383', future_enabled='1')
            def scene(frame):
                with (root/'usa-host-scenes.csv').open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=row);w.writeheader();w.writerow(row | {'frame':str(frame)})
            scene(739)
            self.assertEqual(verify(trial,root)['first'],739)
            with self.assertRaises(ValueError):verify(None,root)
            scene(740)
            with self.assertRaises(ValueError):verify(trial,root)
            scene(739)
            for text in ('', ready+ready, ready.replace('739','5001'), ready.replace('81','82')):
                (root/'stderr.log').write_text(text)
                with self.assertRaises(ValueError):verify(trial,root)
            (root/'stderr.log').write_text(ready)
            (root/'vunit-bootstrap-fast.bin').write_bytes(b'partial')
            with self.assertRaises(ValueError):verify(trial,root)


if __name__ == '__main__':
    unittest.main()
