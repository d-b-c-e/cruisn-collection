import json
import csv
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import cheats
from session_case import Recording, compare_evidence

XML = b'''<mamecheat version="1">
<cheat desc="Infinite Time"><script state="run"><action>maincpu.pb@E634=63</action></script></cheat>
<cheat desc="Finish"><script state="on"><action>maincpu.pb@E634=0</action></script></cheat>
<cheat desc="Instruction patch"><script state="on"><action>temp0=maincpu.pd@1234</action></script><script state="off"><action>maincpu.pd@1234=temp0</action></script></cheat>
<cheat desc="Choice"><parameter><item value="1">First</item><item value="2">Second</item></parameter><script state="run"><action>maincpu.pb@E637=param</action></script></cheat>
</mamecheat>'''


class CheatTests(unittest.TestCase):
    def test_import_uses_only_exact_arcade_paths_and_validates_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); archive=root/'cheat.zip'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('crusnusa.xml',XML);z.writestr('n64/crusnwld24.xml',XML)
                z.writestr('../offroadc.xml',XML)
            self.assertEqual(cheats.import_files(archive,root/'rig'),{'crusnusa':4})
            self.assertEqual(cheats.catalog(root/'rig','crusnwld24')['entries'],[])
            self.assertFalse((root/'offroadc.xml').exists())
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('crusnusa.xml',XML.replace(b'Infinite Time',b'New timer'))
                z.writestr('offroadc.xml',b'not XML')
            with self.assertRaises(Exception): cheats.import_files(archive,root/'rig')
            self.assertEqual((root/'rig/cheats/crusnusa.xml').read_bytes(),XML)

    def test_saved_selections_are_bound_to_revision_and_exact_imported_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            rig=Path(td);(rig/'cheats').mkdir();p=rig/'cheats/crusnusa.xml';p.write_bytes(XML)
            cat=cheats.catalog(rig,'crusnusa')
            self.assertEqual(cheats.selections(rig,cat),{})
            cheats.save(rig,cat,{'1':1,'2':1,'3':1,'4':2})
            self.assertEqual(cheats.selections(rig,cat),{'1':1,'4':2})
            self.assertEqual(cheats.selections(rig,cheats.catalog(rig,'crusnwld24')), {})
            p.write_bytes(XML+b'\n')
            self.assertEqual(cheats.selections(rig,cheats.catalog(rig,'crusnusa')), {})

    def test_pre_race_menu_does_not_activate_one_shots_or_restore_unloaded_code(self):
        rows=cheats.metadata(XML)
        self.assertEqual(rows[0]['choices'],['OFF','ON'])
        self.assertTrue(rows[1]['unavailable']);self.assertTrue(rows[2]['unavailable'])
        self.assertEqual(rows[3]['choices'],['OFF','First','Second'])
        with self.assertRaises(ValueError): cheats.metadata(b'<!DOCTYPE bad><mamecheat version="1"/>')

    def test_recording_freezes_cheats_and_replay_rebinds_all_external_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rig=root/'rig';(rig/'cheats').mkdir(parents=True)
            (rig/'cheats/crusnusa.xml').write_bytes(XML)
            cat=cheats.catalog(rig,'crusnusa');cheats.save(rig,cat,{'1':1})
            bundle=cheats.prepare(Path(__file__).resolve().parents[1],rig,'crusnusa')
            exe=root/'vunit.exe';exe.write_bytes(b'fixture, never launched')
            roms=root/'roms';roms.mkdir();(roms/'crusnusa.zip').write_bytes(b'ROM identity fixture')
            recording=Recording(root/'case',every=60,stop_frame=120)
            with mock.patch('session_case.subprocess.check_output',return_value=b'<mame><machine name="crusnusa"/></mame>'),mock.patch('session_case.git_identity',return_value={}):
                command,env,runtime=recording.prepare([str(exe),'crusnusa','-rompath',str(roms),'-cheatpath',str(bundle),'-cheat'],{'MIDV_CHEATS':str(bundle)},rig)
            self.assertEqual(recording.manifest['settings']['MIDV_CHEATS'],'@initial/cheats')
            self.assertEqual(command[command.index('-cheatpath')+1],str(runtime/'cheats'))
            self.assertEqual(env['MIDV_CHEATS'],str(runtime/'cheats'))
            self.assertEqual((runtime/'cheats/crusnusa.xml').read_bytes(),XML)
            (bundle/'crusnusa.xml').write_bytes(b'changed outside recording')
            self.assertEqual((root/'case/initial/cheats/crusnusa.xml').read_bytes(),XML)

    def test_actions_are_frozen_for_derived_cases_and_hash_checked_on_replay(self):
        from session_case import prepare_run
        from verification import sha256_file
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rig=root/'rig';(rig/'cheats').mkdir(parents=True)
            (rig/'cheats/crusnusa.xml').write_bytes(XML)
            bundle=cheats.prepare(Path(__file__).resolve().parents[1],rig,'crusnusa')
            exe=root/'vunit.exe';exe.write_bytes(b'fixture, never launched')
            roms=root/'roms';roms.mkdir();(roms/'crusnusa.zip').write_bytes(b'fixture')
            actions=root/'parent-actions.csv';actions.write_text('frame,index,steps,activate\n90,2,0,1\n',encoding='utf-8')
            recording=Recording(root/'case',every=60,stop_frame=120)
            with mock.patch('session_case.subprocess.check_output',return_value=b'<mame><machine name="crusnusa"/></mame>'),mock.patch('session_case.git_identity',return_value={}):
                _,_,runtime=recording.prepare([str(exe),'crusnusa','-rompath',str(roms)],
                    {'MIDV_CHEATS':str(bundle)},rig,cheat_actions=actions)
            self.assertEqual((root/'case/initial/cheats/replay-actions.csv').read_bytes(),actions.read_bytes())
            (runtime/'cheats/actions.csv').write_bytes(actions.read_bytes())
            (runtime/'input/session.inp').write_bytes(b'fixture')
            recording.manifest['evidence']={'frames':120,'cheats':{'actions.csv':sha256_file(actions)}}
            prepare_run(root/'case',recording.manifest,root/'replay',playback=True)
            self.assertEqual((root/'replay/cheats/replay-actions.csv').read_bytes(),actions.read_bytes())
            (runtime/'cheats/actions.csv').write_text('frame,index,steps,activate\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'cheat actions changed'):
                prepare_run(root/'case',recording.manifest,root/'tampered',playback=True)

    def test_action_evidence_rejects_events_past_recording_end_or_out_of_order(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'actions.csv';cat={'entries':cheats.metadata(XML)}
            for rows in ('121,2,0,1\n','90,2,0,1\n89,2,0,1\n','90,2,0,2\n','90,99,0,1\n'):
                path.write_text('frame,index,steps,activate\n'+rows,encoding='utf-8')
                with self.assertRaises(ValueError): cheats.read_actions(path,cat,120)
            path.write_text('frame,index,steps,activate\n90,2,0,1\n90,2,0,1\n',encoding='utf-8')
            self.assertEqual(len(cheats.read_actions(path,cat,120)),2)

    def test_all_off_import_still_provides_live_menu_but_absent_catalog_disables_engine(self):
        with tempfile.TemporaryDirectory() as td:
            rig=Path(td); (rig/'cheats').mkdir()
            self.assertIsNone(cheats.prepare(Path(__file__).resolve().parents[1],rig,'crusnusa'))
            (rig/'cheats/crusnusa.xml').write_bytes(XML)
            bundle=cheats.prepare(Path(__file__).resolve().parents[1],rig,'crusnusa')
            selection=json.loads((bundle/'selection.json').read_text(encoding='utf-8'))
            self.assertEqual(selection['selected'],{})
            self.assertEqual(selection['live_protocol'],1)
            self.assertEqual(len(selection['entries']),4)
            self.assertIn('entries={},catalog={', (bundle/'settings.lua').read_text(encoding='utf-8'))

    def test_cheat_state_mismatch_cannot_pass_a_pixel_comparison(self):
        with self.assertRaisesRegex(ValueError,'cheat'):
            compare_evidence('.', '.', {'cheats':{'events.csv':'one'}},{'cheats':{'events.csv':'two'}})

    def test_lua_string_does_not_turn_metadata_into_code(self):
        value='A"; error("no") --\n\u00e9'
        quoted=cheats.lua_string(value)
        self.assertNotIn('error',quoted)
        self.assertTrue(quoted.startswith('"\\065'))

    def test_parameter_menu_preserves_native_clamped_final_step_and_description(self):
        xml = b'<mamecheat version="1"><cheat desc=" Choice "><parameter min="0X2" max="$5" step="#2"/><script state="run"/></cheat></mamecheat>'
        row = cheats.metadata(xml)[0]
        self.assertEqual(row['description'], ' Choice ')
        self.assertEqual(row['choices'], ['OFF','2','4','5'])

    def test_timer_probe_accepts_callback_phase_but_rejects_a_countdown_while_on(self):
        from check_cheats import inspect
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'cheat-probe.csv'
            rows=[]
            for frame in range(2500,3301):
                on=2600<=frame<3000
                value=(99 if frame%60 else 98) if on else max(0,99-(frame-3000)//60)
                rows.append([frame,value,0,'On' if on else 'Off'])
            def write():
                with path.open('w',newline='') as out:
                    writer=csv.writer(out);writer.writerow(['frame','timer','timer_high','state']);writer.writerows(rows)
            write();self.assertEqual(inspect(td,'crusnusa')['on_samples'],300)
            rows[300][1]=97;write()
            with self.assertRaisesRegex(ValueError,'enabled timer'):inspect(td,'crusnusa')
            for row in rows:
                row[1],row[2]=(0,1+row[0]%2) if row[3]=='On' else ((row[0]-3000)//60,0)
            write();self.assertEqual(inspect(td,'offroadc')['on_values'],[(0,1),(0,2)])
            rows[300][1]=1;write()
            with self.assertRaisesRegex(ValueError,'enabled timer'):inspect(td,'offroadc')
