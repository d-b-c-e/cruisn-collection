import argparse
import csv
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_scene_options import add_arguments, configure, validate_runtime
from exotica_future_gpu import framebuffer, verify


class ExoticaFutureGpu(unittest.TestCase):
    def args(self, *words):
        p = argparse.ArgumentParser(); p.add_argument('--candidate'); add_arguments(p)
        return p.parse_args(words)

    def test_recording_compatibility_and_dependencies(self):
        old = dict(MIDZ_GL='1', MIDV_FFB='80'); saved = dict(old)
        self.assertIsNone(configure(self.args(), 'crusnexo', old)); self.assertEqual(old, saved)
        words = ('--candidate', 'x.exe', '--exotica-host-scene', 'observe',
                 '--exotica-host-first', '5000', '--exotica-host-last', '5002',
                 '--exotica-host-future', 'draw')
        with self.assertRaisesRegex(ValueError, 'private materials'):
            configure(self.args(*words), 'crusnexo', {})
        a = self.args(*words, '--exotica-host-materials', 'observe')
        settings = dict(MIDZ_GL='1', MIDZ_DEPTH_MIRROR='2', MIDZ_DEPTH_FIRST='2', MIDZ_DEPTH_LAST='5010')
        trial = configure(a, 'crusnexo', settings); self.assertEqual(trial['future'], 2)
        validate_runtime(trial, a, settings)
        saved = dict(settings)
        replay = configure(self.args(), 'crusnexo', settings)
        validate_runtime(replay, self.args(), settings); self.assertEqual(settings, saved)
        for key, value in [('MIDZ_DEPTH_MIRROR', '1'), ('MIDZ_GL_NATIVE', '1'), ('MIDZ_DEPTH_STREAM_FRAME', '5001')]:
            with self.assertRaisesRegex(ValueError, 'live GL/wide depth'):
                validate_runtime(trial, a, dict(settings, **{key: value}))
        with self.assertRaisesRegex(ValueError, 'completed-frame'):
            validate_runtime(trial, a, dict(settings, MIDZ_DEPTH_LAST='5002'))
        settings['MIDZ_HOST_FUTURE'] = '3'
        with self.assertRaisesRegex(ValueError, 'recorded Exotica future'):
            configure(self.args(), 'crusnexo', settings)
        configure(self.args('--candidate', 'x.exe', '--exotica-host-scene', 'off'), 'crusnexo', settings)
        self.assertNotIn('MIDZ_HOST_FUTURE', settings)

    def test_private_page_protection_and_observe(self):
        color = bytes(512*1024*4); depth = struct.pack('<f', 1.)*(512*1024)
        after = bytearray(color); after[100*512*4] = 1
        result = framebuffer([color, depth, after, depth], 0, 0, True)
        self.assertEqual(result['color_differences'], 1)
        with self.assertRaisesRegex(ValueError, 'observe changed'):
            framebuffer([color, depth, after, depth], 0, 0, False)
        with self.assertRaisesRegex(ValueError, 'another page'):
            framebuffer([color, depth, after, depth], 0, 400, True)
        bad = bytearray(depth); struct.pack_into('<f', bad, 0, float('nan'))
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            framebuffer([color, depth, color, bad], 0, 0, True)

    def test_receipt_rejects_undelivered_or_changed_quads(self):
        source = dict(scene='3', frame='5001', multiplier='3', quads='1', hash='123456789abcdef0')
        received = dict(source, mode='2', page='0', vertices='6', bytes=str(32+96+264), snapshot='0', host_us='1.5')
        text = 'MIDZ_HOST_FUTURE=2\nMIDZ_HOST_FUTURE_GPU_RESULT complete=1 scenes=1 quads=1 snapshots=0 written=0 failed=0 rejected=0\n'
        with tempfile.TemporaryDirectory() as tmp:
            def write(name, row):
                with (Path(tmp)/name).open('w', encoding='utf-8', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=list(row)); w.writeheader(); w.writerow(row)
            write('exotica-future-gpu.csv', received)
            write('exotica-host-materials.csv', dict(scene='3', frame='5001', bytes='96'))
            self.assertTrue(verify(tmp, [source], text, 2, [])['passed'])
            write('exotica-future-gpu.csv', dict(received, hash='223456789abcdef0'))
            with self.assertRaisesRegex(ValueError, 'ordered scene'):
                verify(tmp, [source], text, 2, [])
            with self.assertRaisesRegex(ValueError, 'completion/writer'):
                verify(tmp, [source], text.replace('complete=1', 'complete=0'), 2, [])


if __name__ == '__main__':
    unittest.main()
