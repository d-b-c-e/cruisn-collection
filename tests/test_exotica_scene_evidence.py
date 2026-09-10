import copy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from scenery_c31 import F
from verify_exotica_scene import (context_bytes, expected_bytes, explicit_texture,
                                 join_context, unique_frame)


class ExoticaSceneEvidence(unittest.TestCase):
    def scene(self):
        f = lambda n: F.integer(n).store()
        identity = [f(i % 4 == 0) for i in range(9)]
        obj = [0]*32;obj[1:4] = [f(0), f(0), f(100)]
        row = dict(id=1, flags=0, object_words=obj, camera=[f(0)]*3, view=identity,
                   rotation=identity[:], alternate=identity[:], scale=0xfa000000,
                   metadata=[0, 0, 0, 0x100, 6], native_frame=4999, time=1.)
        model = dict(id=1, base=0x100, count=6, translation=[0., 0., 1.5625, 0.],
                     matrix=[float(i % 4 == 0) for i in range(9)], light=[0.]*3,
                     frame=5000, time=1.001, render_policy=0, quad_size=10,
                     ucode=0xc0, palette=0, texture=0, yscale=0, zoffset=0,
                     regs=[0]*128, render=[0]*80)
        return row, model

    def test_exact_context_join_rejects_ambiguity_time_and_camera(self):
        row, model = self.scene()
        joined = join_context([row], [model], row['camera'], row['view'])
        self.assertEqual(joined[3]['chosen_call'], 1)
        with self.assertRaisesRegex(ValueError, 'ambiguous scene CPU/device'):
            join_context([row, row], [model], row['camera'], row['view'])
        with self.assertRaisesRegex(ValueError, 'snapshot camera'):
            join_context([row], [dict(model, time=1.02)], row['camera'], row['view'])
        with self.assertRaisesRegex(ValueError, 'snapshot camera'):
            join_context([row], [model], [0, 0, 0], row['view'])
        with self.assertRaisesRegex(ValueError, 'legacy render policy'):
            join_context([row], [dict(model, render_policy=1)], row['camera'], row['view'])
        second = copy.deepcopy(row);second['id'] = 2;second['time'] = 2.;second['alternate'][0] += 1
        with self.assertRaisesRegex(ValueError, 'billboard rotation'):
            join_context([row, second], [model, dict(model, time=2.001)], row['camera'], row['view'])

    def test_band_filter_preserves_instance_offsets_and_empty_third_band(self):
        rows = [dict(header=[0]*9, band=2, raw=b'b'*520, viewport=2),
                dict(header=[1]*9, band=1, raw=b'a'*260, viewport=1)]
        q1, h1, s1 = expected_bytes(rows, 1)
        self.assertEqual(q1, b'a'*260)
        self.assertEqual(struct.unpack('<11I', h1)[9:], (0, 1))
        q2, h2, s2 = expected_bytes(rows, 2)
        self.assertEqual(q2, b'b'*520+b'a'*260)
        self.assertEqual(struct.unpack_from('<11I', h2, 44)[9:], (2, 1))
        self.assertEqual(expected_bytes(rows, 3), (q2, h2, s2))
        self.assertEqual((s1['viewport_quads'], s2['viewport_quads']), (1, 3))

    def test_texture_must_precede_first_polygon_and_format_is_required(self):
        polygon = [0x38000000]+[0]*9
        prefix = [0x229d0000, 1, 0x36200000, 0x05000100]
        explicit_texture(prefix+polygon, 10)
        for bad in (polygon+prefix, prefix[:2]+polygon, prefix[2:]+polygon):
            with self.assertRaisesRegex(ValueError, 'inherited model texture'):
                explicit_texture(bad, 10)
        with self.assertRaisesRegex(ValueError, 'incomplete model'):
            explicit_texture(prefix+polygon[:-1], 10)

    def test_frame_and_context_boundaries(self):
        with self.assertRaisesRegex(ValueError, 'duplicate scene frame'):
            unique_frame([dict(frame=5000)]*2, 5000)
        for multiplier, margin, fade, policy in ((4, 88, 0, 0), (3, float('nan'), 0, 0),
                                                (3, 88, 2, 0), (3, 88, 0, 1)):
            with self.assertRaisesRegex(ValueError, 'context bounds/policy'):
                context_bytes(5000, multiplier, margin, fade, {}, {}, dict(render_policy=policy), [], [], [])
