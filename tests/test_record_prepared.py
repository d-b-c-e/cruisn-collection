from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import record_prepared as recorder
from verification import sha256_file,write_json
from session_case import tree_hashes


class PreparedRecordingTests(unittest.TestCase):
    def fixture(self,root):
        plan=root/'plan';plan.mkdir();runtime=plan/'run';runtime.mkdir()
        (runtime/'initial.txt').write_text('preserved',encoding='utf-8')
        case=root/'parent';case.mkdir();write_json(case/'case.json',dict(rom='crusnusa',every=60))
        exe=root/'candidate.exe';exe.write_bytes(b'candidate')
        value=dict(schema=1,prepared=True,executed=False,physical_force=False,
            command=[str(exe),'crusnusa','-playback','session.inp','-exit_after_playback'],
            cwd=str(runtime),runtime_hashes=tree_hashes(runtime),case=str(case),case_sha256=sha256_file(case/'case.json'),
            executable_sha256=sha256_file(exe),candidate_dependencies={},environment={'MIDV_FFB':'0'})
        report=dict(prepared_only=True,executed=False,passed=False,
            scenery_preset=dict(name='continuous-3x',rom='crusnusa'))
        def save():
            write_json(plan/'launch-plan.json',value)
            report['launch_plan_sha256']=sha256_file(plan/'launch-plan.json')
            write_json(plan/'report.json',report)
        save();return plan,value,report,save

    def test_live_command_removes_all_playback_and_stop_options_preserving_bindings(self):
        original=['candidate','crusnusa','-playback','one','-record','old','-ctrlr','Wheel',
                  '-exit_after_playback','-seconds_to_run','15','-frames_to_run','100','-playback','two','-joystick']
        got=recorder.live_command(original)
        self.assertEqual(got,['candidate','crusnusa','-ctrlr','Wheel','-joystick','-seconds_to_run','0'])
        self.assertIn('-playback',original)
        for extra in (['-playback'],['-playback','-window'],['-nojoystick'],['-nomouse'],['-nolightgun']):
            with self.subTest(extra=extra),self.assertRaises(ValueError):recorder.live_command(['exe','rom']+extra)

    def test_changed_dependencies_and_unsafe_capture_plans_reject(self):
        with tempfile.TemporaryDirectory() as td:
            plan,value,report,save=self.fixture(Path(td))
            self.assertEqual(recorder.load_plan(plan)[2]['rom'],'crusnusa')
            for key,v in (('MIDV_FFB','1'),('MIDV_FFB_TEST','0'),('MIDV_TELEM_FORZA','127.0.0.1:5300'),
                          ('SNAP_PROBE_SCRIPT','probe.lua'),('MIDZ_GL_SNAP','old'),('MIDZ_HOST_SNAPSHOTS','5219'),
                          ('MIDZ_MODEL_ENDPOINT_SNAPSHOT','5219')):
                old=dict(value['environment']);value['environment'][key]=v;save()
                with self.subTest(key=key),self.assertRaises(ValueError):recorder.load_plan(plan)
                value['environment']=old
            save();(plan/'run/initial.txt').write_text('changed',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'initial state'):recorder.load_plan(plan)
            (plan/'run/initial.txt').write_text('preserved',encoding='utf-8')
            dependency=Path(value['command'][0]).parent/'force-profiles.ini';dependency.write_text('changed',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'dependencies changed'):recorder.load_plan(plan)
            dependency.unlink()
            Path(value['command'][0]).write_bytes(b'other')
            with self.assertRaisesRegex(ValueError,'candidate changed'):recorder.load_plan(plan)

    def test_prepare_only_freezes_live_case_and_never_executes_or_opens_clock(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,value,_,_=self.fixture(root);out=root/'recording'
            class FakeRecording:
                def __init__(self,path,**kwargs):
                    self.path=path;self.path.mkdir();self.manifest={}
                    self.options=kwargs
                def prepare(self,command,env,rig):
                    assert '-playback' not in command and env['MIDV_FFB']=='0'
                    assert rig==plan/'run' and self.options['stop_frame']==0
                    runtime=self.path/'record';runtime.mkdir()
                    return command+['-record','session.inp'],env,runtime
            with patch.object(recorder,'Recording',FakeRecording),patch.object(recorder,'execute') as execute,patch.object(recorder,'SessionClock') as clock:
                self.assertEqual(recorder.main([str(plan),'--output',str(out),'--title','Open course','--prepare-only']),0)
                execute.assert_not_called();clock.assert_not_called()
            result=json.loads((out/'report.json').read_text(encoding='utf-8'))
            self.assertTrue(result['prepared']);self.assertFalse(result['executed']);self.assertFalse(result['recorded'])
            command=json.loads((out/'live-launch.json').read_text(encoding='utf-8'))['command']
            self.assertIn('-record',command);self.assertNotIn('-playback',command)


if __name__=='__main__':unittest.main()
