import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from gl_frames import (compare_completed_frames, read_completed_frames, main,
                       requested_frames, recorded_capture_request, IncompleteCaptureError,
                       completion_drain_target)


class CompletedGlTests(unittest.TestCase):
    def test_zeus_drain_covers_scenes_after_last_screenshot(self):
        self.assertEqual(completion_drain_target('MIDZ',5300,range(5216,5271)),5299)
        self.assertEqual(completion_drain_target('MIDZ',5300,depth_observation=True),5299)
        self.assertIsNone(completion_drain_target('MIDZ',5300))
        self.assertEqual(completion_drain_target('MIDV',5300,[5270]),5270)
        self.assertEqual(completion_drain_target('MIDV',5300,[5300]),5300)
        with self.assertRaises(ValueError):completion_drain_target('MIDZ',5300,[5300])
        with self.assertRaises(ValueError):completion_drain_target('MIDV',5300,depth_observation=True)

    def run_fixture(self, path, prefix='MIDZ', frames=(6538, 6545)):
        path.mkdir()
        self.fixture(path/'gl-snap', frames)
        env = {prefix+'_GL': '1', prefix+'_GL_SNAP': 'archived/path/is/not/followed',
               prefix+'_GL_SNAP_FIRST': '6536', prefix+'_GL_SNAP_LAST': '6550',
               prefix+'_GL_SNAP_EVERY': '7', prefix+'_GL_SNAP_MAX': '3', 'SNAP_STOP': '6552'}
        (path/'invocation.json').write_text(json.dumps({'environment': env}))
        return env

    def test_run_comparison_uses_actual_global_cadence_and_receipt_dimensions(self):
        for prefix in ('MIDV', 'MIDZ'):
            with self.subTest(renderer=prefix), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); a,b=root/'a',root/'b'
                self.run_fixture(a,prefix); self.run_fixture(b,prefix)
                report=root/'report.json'
                self.assertEqual(main([str(a),str(b),'--run-directories','--report',str(report)]),0)
                result=json.loads(report.read_text())
                self.assertEqual(result['frames'],2)
                self.assertEqual(result['capture_requests'][0]['expected_frames'],[6538,6545])
                self.assertEqual(result['capture_requests'][0]['renderer'],prefix)

    def test_run_comparison_rejects_missing_images_even_when_both_runs_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); a,b=root/'a',root/'b'
            self.run_fixture(a,frames=(6538,)); self.run_fixture(b,frames=(6538,))
            report=root/'report.json'
            self.assertEqual(main([str(a),str(b),'--run-directories','--report',str(report)]),1)
            self.assertEqual(json.loads(report.read_text())['capture_diagnostics']['missing_frames'],[6545])

    def test_recorded_capture_request_rejects_ambiguous_or_incomplete_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'run';env=self.run_fixture(path)
            for change in ({'MIDZ_GL_SNAP_MAX':'1'}, {'SNAP_STOP':'6545'},
                           {'MIDZ_GL_SNAP_EVERY':None}, {'MIDV_GL':'1','MIDV_GL_SNAP':'also-active'}):
                with self.subTest(change=change):
                    (path/'invocation.json').write_text(json.dumps({'environment':dict(env,**change)}))
                    with self.assertRaises(ValueError): recorded_capture_request(path)

    def test_stop_frame_requires_a_completed_frame_before_shutdown(self):
        self.assertEqual(list(requested_frames(10,20,3,stop_frame=20)),[12,15,18])
        self.assertEqual(list(requested_frames(7180,7219,1,40,stop_frame=7220)),list(range(7180,7220)))
        for last in (7220,7221):
            with self.subTest(last=last),self.assertRaisesRegex(ValueError,'precede the replay stop frame'):
                requested_frames(7180,last,1,stop_frame=7220)

    def test_capture_preflight_counts_global_cadence(self):
        self.assertEqual(list(requested_frames(9240, 9240, 1, 1)), [9240])
        self.assertEqual(list(requested_frames(31, 35, 2, 2)), [32, 34])
        for args in ((31,35,2,1), (31,31,2), (0,10,0), (-1,5,1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                requested_frames(*args)

    def test_incomplete_capture_retains_missing_and_unexpected_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'run'
            self.fixture(path, (30,32,35))
            with self.assertRaises(IncompleteCaptureError) as caught:
                read_completed_frames(path, iter((30,32,34,36)))
            report = caught.exception.capture_diagnostics
            self.assertEqual(report['missing_frames'], [34,36])
            self.assertEqual(report['unexpected_frames'], [35])
            self.assertEqual(report['captured_count'], 3)
            self.assertEqual(report['last_captured'], 35)
            self.assertEqual(report['dimensions'], [(3,2)])

    def fixture(self, path, frames=(30, 31), dropped=0, color="red"):
        path.mkdir()
        with (path / "captures.csv").open("w", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(("file", "last_received_frame", "completed_frame", "width", "height", "dropped_messages"))
            for i, frame in enumerate(frames):
                name = f"{i}.png"
                Image.new("RGB", (3, 2), color).save(path / name)
                writer.writerow((name, frame, frame, 3, 2, dropped))

    def test_pixel_change_is_not_a_passing_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a", Path(tmp) / "b"
            self.fixture(a)
            self.fixture(b, color="blue")
            self.assertEqual(compare_completed_frames(a, a, range(30, 32))["frames"], 2)
            self.assertEqual(compare_completed_frames(a, b)["different_frames"], [30, 31])

    def test_missing_duplicate_and_dropped_frames_fail(self):
        for frames, dropped in (((30,), 0), ((30, 30), 0), ((30, 31), 1)):
            with self.subTest(frames=frames, dropped=dropped), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "run"
                self.fixture(path, frames, dropped)
                with self.assertRaises(ValueError):
                    read_completed_frames(path, range(30, 32))

    def test_sparse_pixel_evidence_and_reused_file_rejection(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / 'a', root / 'b'
            self.fixture(a, (30, 32, 34))
            self.fixture(b, (30, 32, 34))
            with Image.open(b / '1.png') as im:
                im.putpixel((2, 1), (0, 0, 255))
                im.save(b / '1.png')
            report, sheet = root / 'report.json', root / 'sheet.png'
            self.assertEqual(main([str(a), str(b), '--frames', '30:34', '--every', '2',
                                   '--details', '--contact-sheet', str(sheet), '--report', str(report)]), 1)
            data = json.loads(report.read_text())
            self.assertNotIn('error', data)
            self.assertEqual(data['different_frames'], [32])
            self.assertEqual(data['pixel_changes'][0]['changed_pixels'], 1)
            self.assertEqual(data['pixel_changes'][0]['bounds_xyxy_exclusive'], [2, 1, 3, 2])
            self.assertTrue(sheet.is_file())
            receipts = (b / 'captures.csv').read_text().replace('1.png', '0.png')
            (b / 'captures.csv').write_text(receipts)
            with self.assertRaisesRegex(ValueError, 'filename was reused'):
                read_completed_frames(b)

    def test_dark_pixel_triage_keeps_exact_comparison_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); a,b=root/'a',root/'b'
            self.fixture(a, (30,), color='white')
            self.fixture(b, (30,), color='white')
            with Image.open(a/'0.png') as im:
                im.putpixel((0,0),(0,0,0))
                im.save(a/'0.png')
            with Image.open(b/'0.png') as im:
                im.putpixel((1,1),(3,3,3))
                im.save(b/'0.png')
            report=compare_completed_frames(a,b,(30,),details=True)
            self.assertFalse(report['passed'])
            self.assertEqual(report['different_frames'],[30])
            row=report['pixel_changes'][0]
            self.assertEqual(row['changed_pixels'],2)
            self.assertEqual(row['candidate_new_near_black'],1)
            self.assertEqual(row['candidate_recovered_near_black'],1)
            self.assertEqual(row['new_near_black_bounds_xyxy_exclusive'],[1,1,2,2])
            self.assertEqual(sum(map(sum,row['changed_pixels_by_thirds'])),2)

    def test_sparse_cadence_matches_global_native_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root / 'run', (32, 34))
            self.assertEqual(main([str(root/'run'), str(root/'run'), '--frames', '31:35',
                '--every', '2', '--report', str(root/'report.json')]), 0)
            self.assertTrue(compare_completed_frames(root/'run', root/'run', iter((32, 34)))['passed'])
