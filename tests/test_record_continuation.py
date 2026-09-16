from pathlib import Path
import csv
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from record_continuation import compare_prefix
import record_continuation
import test_synthetic_input as synthetic
from synthesize_input import ANALOG_LAYOUTS


class ContinuationPrefixTests(unittest.TestCase):
    def test_record_command_keeps_provenance_and_disables_physical_force(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); parent = root/'parent'; output = root/'new'
            (parent/'record/input').mkdir(parents=True)
            (parent/'initial').mkdir()
            (parent/'record/input/session.inp').write_bytes(synthetic.SyntheticInputTests().seed())
            trace = 'frame,emulated_seconds,host_seconds,speed_percent,:WHEEL\n1,.01,1,1,128\n2,.02,2,1,128\n'
            (parent/'record/frames.csv').write_text(trace,encoding='utf-8')
            manifest = dict(command=['old.exe','crusnusa'],rom='crusnusa',every=1,
                            evidence=dict(frames=2),settings=dict(MIDV_FFB='1',MIDV_GL_SNAP='old-path'))
            (parent/'case.json').write_text(json.dumps(manifest),encoding='utf-8')
            scenario = root/'tail.json'
            scenario.write_text(json.dumps(dict(frames=1,analog={
                tag:[[0,0]] for tag in ANALOG_LAYOUTS['crusnusa']})),encoding='utf-8')
            with patch.object(record_continuation,'validate_parent') as validation, \
                 patch.object(record_continuation,'Recording') as factory, \
                 patch.object(record_continuation,'execute') as execution:
                recording = factory.return_value
                recording.path = output/'case'; recording.manifest = {'status':'recorded'}
                runtime = recording.path/'record'
                def prepare(command,env,initial,**kwargs):
                    runtime.mkdir(parents=True)
                    (runtime/'frames.csv').write_text(trace+'3,.03,3,1,128\n',encoding='utf-8')
                    return command,env,runtime
                recording.prepare.side_effect = prepare
                execution.return_value = dict(returncode=0,error=None)
                self.assertEqual(record_continuation.main([str(parent),str(scenario),
                    '--candidate',str(root/'candidate.exe'),'--output',str(output),'--title','Test tail']),0)
                validation.assert_called_once()
                execution.assert_called_once()
                self.assertEqual(execution.call_args.args[2]['MIDV_FFB'],'0')
                self.assertNotIn('MIDV_GL_SNAP',execution.call_args.args[2])
                self.assertEqual(factory.call_args.kwargs['stop_frame'],3)
                report = json.loads((output/'report.json').read_text(encoding='utf-8'))
                self.assertTrue(report['passed']); self.assertEqual(report['original_inputs_exact'],2)
                self.assertEqual(recording.manifest['derived_from']['kind'],'recorded-prefix-with-synthetic-tail')

    def test_original_input_and_time_are_exact_but_host_speed_can_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fields = ['frame', 'emulated_seconds', 'host_seconds', 'speed_percent', ':WHEEL']
            original = [[1, .01, 1, 1, 100], [2, .02, 2, 1, 200]]
            tail = [[1, .01, 11, .8, 100], [2, .02, 12, .9, 200], [3, .03, 13, 1, 128]]
            def write(name, rows, columns=fields):
                path = root/name
                with path.open('w', encoding='utf-8', newline='') as stream:
                    writer = csv.writer(stream); writer.writerow(columns); writer.writerows(rows)
                return path
            a = write('parent.csv', original)
            b = write('recorded.csv', tail)
            self.assertEqual(compare_prefix(a,b,2,3), dict(original_inputs_exact=2,tail_frames=1))
            with self.assertRaisesRegex(ValueError,'extend the complete original'):
                compare_prefix(a,b,2,1)
            for index, value in ((1,.011),(4,101)):
                changed = [row[:] for row in tail]; changed[0][index] = value
                write('recorded.csv', changed)
                with self.assertRaisesRegex(ValueError,'changed original input/time at frame 1'):
                    compare_prefix(a,b,2,3)
            write('recorded.csv', tail[:-1])
            with self.assertRaisesRegex(ValueError,'complete frame counts'):
                compare_prefix(a,b,2,3)
            write('recorded.csv', tail, fields[:-1]+[':BRAKE'])
            with self.assertRaisesRegex(ValueError,'columns'):
                compare_prefix(a,b,2,3)


if __name__ == '__main__':
    unittest.main()
