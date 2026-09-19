"""Pure synthetic contract tests; never import UI, DirectInput, SDL or an emulator."""
import configparser
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'harness'))
import control_preferences as C

PRODUCT = '0006346e-0000-0000-0000-504944564944'
INSTANCE = '11111111-2222-3333-4444-555555555555'
OTHER = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
IDENTITY = dict(backend='dinput', product_guid=PRODUCT, instance_guid=INSTANCE)
PATH = r'\\?\HID#VID_346E&PID_0006#fixture'
STEER = dict(version=1, kind='steering', left=-0.8, centre=0.2, right=1.0, invert=False, deadzone=0.1)
PEDAL = dict(version=1, kind='pedal', released=1.0, full=-1.0, invert=False, deadzone=0.0)


def device(identity=None, name='Fixture Wheel', axes=C.AXES):
    return dict(identity=deepcopy(identity or IDENTITY), name=name, axes=list(axes))


def proposal(action='steer', calibration=STEER, identity=IDENTITY, legacy_binding=None):
    return C.make_proposal(action, identity, 'XAXIS' if action == 'steer' else 'ZAXIS',
                           calibration, legacy_binding=legacy_binding)


class IdentityTests(unittest.TestCase):
    def test_exact_identity_survives_reorder_and_friendly_rename(self):
        requested = {**IDENTITY, 'product_guid': '{'+PRODUCT.upper()+'}'}
        twin = device({**IDENTITY, 'instance_guid': OTHER})
        target = device(name='Renamed display')
        for rows in ([twin, target], [target, twin]):
            result = C.resolve_device(requested, rows)
            self.assertEqual(result['status'], 'resolved')
            self.assertEqual(result['device']['name'], 'Renamed display')
        self.assertEqual(requested['product_guid'], '{'+PRODUCT.upper()+'}')

    def test_missing_ambiguous_invalid_never_return_device(self):
        cases = [([], 'missing'), ([device({**IDENTITY, 'instance_guid': OTHER})], 'missing'),
                 ([device(), device()], 'ambiguous'), ([device(), {}], 'invalid')]
        for rows, status in cases:
            with self.subTest(status=status):
                self.assertEqual(C.resolve_device(IDENTITY, rows), dict(status=status, device=None))
        self.assertEqual(C.resolve_device({**IDENTITY, 'backend':'sdl'}, [device()])['status'], 'invalid')
        self.assertEqual(C.resolve_device(None, [device()])['status'], 'invalid')

    def test_product_and_instance_both_required_no_name_vidpid_fallback(self):
        other_product = {**IDENTITY, 'product_guid': OTHER}
        self.assertEqual(C.resolve_device(other_product, [device()])['status'], 'missing')
        for bad in ('', '346e:0006', INSTANCE+'junk', '{'+INSTANCE, '00000000-0000-0000-0000-000000000000'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                C.canonical_identity({**IDENTITY, 'instance_guid':bad})

    def test_hid_path_is_optional_current_metadata_not_stable_input_key(self):
        saved = {**IDENTITY, 'hid_path': PATH+'old', 'ffb_capable':True}
        self.assertIsNone(C.output_path(C.resolve_device(saved, [device()])))
        current = {**IDENTITY, 'hid_path':PATH, 'ffb_capable':True}
        result = C.resolve_device(saved, [device(current)])
        self.assertEqual(C.output_path(result), PATH.upper())
        incapable = C.resolve_device(saved, [device({**current, 'ffb_capable':False})])
        self.assertFalse(incapable['device']['identity']['ffb_capable'])
        self.assertIsNone(C.output_path(incapable))
        self.assertIsNone(C.output_path(C.resolve_device(saved, [])))
        for extra in ({'hid_path':''}, {'hid_path':'Wheel'}, {'hid_path':PATH+'\n'}, {'ffb_capable':1}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                C.canonical_identity({**IDENTITY, **extra})

    def test_legacy_match_only_proposes_exact_unique_name_without_mutation(self):
        rows = [device()]
        before = deepcopy(rows)
        answer = C.propose_legacy_identity('fixture wheel', rows)
        self.assertEqual(answer['status'], 'proposal')
        self.assertEqual(answer['identity'], IDENTITY)
        self.assertEqual(rows, before)
        self.assertEqual(C.propose_legacy_identity('Wheel', rows)['status'], 'missing')
        self.assertEqual(C.propose_legacy_identity('Fixture Wheel', rows+rows)['status'], 'ambiguous')
        self.assertEqual(C.propose_legacy_identity('Fixture Wheel', [{}])['status'], 'invalid')


class CalibrationTests(unittest.TestCase):
    def test_known_action_kinds_cannot_silently_change_output_domain(self):
        with self.assertRaisesRegex(ValueError, 'requires steering'):
            proposal(calibration=PEDAL)
        for action in ('gas', 'brake', 'clutch', 'handbrake'):
            with self.subTest(action=action), self.assertRaisesRegex(ValueError, 'requires pedal'):
                proposal(action=action,calibration=STEER)

    def test_independent_golden_vectors_for_native_adapter(self):
        fixture = json.loads((ROOT/'fixtures/control-calibration.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(fixture['version'], 1)
        count = 0
        for vector in fixture['vectors']:
            for raw, expected in vector['samples']:
                with self.subTest(vector=vector['name'], raw=raw):
                    self.assertAlmostEqual(C.normalize(raw, vector['calibration']), expected,
                                           delta=fixture['absolute_tolerance'])
                count += 1
        self.assertEqual(count, 57)

    def test_invalid_ranges_versions_types_and_nonfinite_values(self):
        bads = [dict(STEER, version=2), dict(STEER, version=True), dict(STEER, left=0.2),
                dict(STEER, right=0.22), dict(STEER, centre=1.1), dict(STEER, centre=-0.9),
                dict(STEER, invert=1), dict(STEER, deadzone=1), dict(STEER, deadzone=-0.1),
                dict(STEER, deadzone=float('nan')), dict(STEER, unknown=1),
                dict(PEDAL, full=0.99), dict(PEDAL, released=float('inf'))]
        for bad in bads:
            with self.subTest(bad=bad), self.assertRaises(ValueError): C.validate_calibration(bad)
        for bad in (float('nan'), float('inf'), -float('inf'), True, '0', 1.01, -1.01, 10**1000):
            with self.subTest(raw=repr(bad)[:25]), self.assertRaises(ValueError): C.normalize(bad, None)

    def test_null_calibration_is_exact_raw_passthrough_not_pedal_rescale(self):
        for value in (-1, -0.375, 0, 0.125, 1): self.assertEqual(C.normalize(value, None), value)
        self.assertIsNone(C.validate_calibration(None))
        original = deepcopy(STEER)
        C.normalize(-0.3, STEER)
        self.assertEqual(STEER, original)

    def test_deadzone_applied_once_and_monotonic_after_capture_direction(self):
        normal = dict(PEDAL, released=-1, full=1, deadzone=0.2)
        self.assertAlmostEqual(C.normalize(0.2, normal), 0.5)
        values = [C.normalize(-1+i/100, normal) for i in range(201)]
        self.assertEqual(values, sorted(values))
        steering = dict(STEER, invert=False)
        values = [C.normalize(-1+i/100, steering) for i in range(201)]
        self.assertEqual(values, sorted(values))


class DraftTests(unittest.TestCase):
    def draft(self, kind='steering'):
        return C.CalibrationDraft('steer' if kind=='steering' else 'gas', IDENTITY, 'XAXIS', kind,
                                  original=proposal()['record'])

    def test_steering_stages_asymmetry_review_then_explicit_proposal(self):
        draft = self.draft()
        before = draft.original
        for step, raw in (('centre',0.2),('left',-0.8),('right',1),('return',0.21)):
            draft.capture(step, raw, IDENTITY)
        self.assertEqual(draft.status, 'ready')
        proposed = draft.proposal(deadzone=0.1)
        self.assertEqual(proposed['record']['calibration'], STEER)
        self.assertEqual(draft.original, before)
        proposed['record']['identity']['instance_guid'] = OTHER
        self.assertEqual(draft.proposal()['record']['identity'], IDENTITY)

    def test_reversed_steering_and_high_rest_pedal_capture(self):
        draft = self.draft()
        for step, raw in (('centre',0.1),('left',0.9),('right',-0.7),('return',0.1)):
            draft.capture(step, raw, IDENTITY)
        self.assertEqual(C.normalize(-0.7, draft.proposal()['record']['calibration']), 1)
        pedal = self.draft('pedal')
        for step, raw in (('released',1),('full',-1),('return',1)):
            pedal.capture(step, raw, IDENTITY)
        self.assertEqual(pedal.proposal()['record']['calibration'], PEDAL)

    def test_cancel_and_incomplete_review_retain_original(self):
        draft = self.draft()
        before = draft.original
        with self.assertRaises(ValueError): draft.proposal()
        draft.capture('centre',0.2,IDENTITY)
        self.assertEqual(draft.cancel(), before)
        self.assertEqual(draft.status, 'cancelled')
        with self.assertRaises(ValueError): draft.proposal()
        self.assertEqual(draft.original, before)
        self.assertEqual(draft.samples,{})

    def test_disconnection_ambiguity_and_axis_loss_cancel_without_replacement(self):
        for inventory in ([], [device(),device()], [device(axes=['YAXIS'])]):
            draft = self.draft()
            before = draft.original
            draft.capture('centre',0.2,IDENTITY)
            self.assertEqual(draft.observe_inventory(inventory), 'disconnected')
            self.assertEqual(draft.original,before)
            self.assertEqual(draft.observe_inventory([device()]),'disconnected')
            with self.assertRaises(ValueError): draft.proposal()

    def test_changed_or_invalid_identity_discards_draft(self):
        for identity in ({**IDENTITY, 'instance_guid':OTHER}, {'backend':'dinput'}):
            draft = self.draft()
            with self.assertRaises(ValueError): draft.capture('centre',0.2,identity)
            self.assertEqual(draft.status, 'disconnected')
            self.assertEqual(draft.original, proposal()['record'])

    def test_step_order_return_check_and_invalid_span_do_not_produce_proposal(self):
        draft = self.draft()
        with self.assertRaises(ValueError): draft.capture('left',-0.8,IDENTITY)
        for step, raw in (('centre',0.2),('left',-0.8),('right',1)):
            draft.capture(step,raw,IDENTITY)
        with self.assertRaises(ValueError): draft.capture('return',0.6,IDENTITY)
        self.assertEqual(draft.status,'capturing')
        draft.capture('return',0.2,IDENTITY)
        self.assertEqual(draft.status,'ready')
        pedal=self.draft('pedal')
        pedal.capture('released',0,IDENTITY);pedal.capture('full',0.01,IDENTITY)
        with self.assertRaises(ValueError): pedal.capture('return',0,IDENTITY)
        with self.assertRaises(ValueError): pedal.proposal()


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'collection.ini'
        self.original = (b'\xef\xbb\xbf[collection]\r\nffb_enabled=0\r\nffb=63\r\nowner_note=100% custom\r\n'
                         b'[wheelmap]\r\nsteer=Old wheel|axis:0:0:pos\r\ngear1=Shifter|btn:6\r\n'
                         b'[telemetry]\r\nforza=192.0.2.10:8000\r\n[Owner]\r\nMixedCase=kept\r\n')
        self.path.write_bytes(self.original)

    def read(self):
        cp=configparser.ConfigParser(interpolation=None);cp.optionxform=str
        cp.read(self.path,encoding='utf-8-sig');return cp

    def test_atomic_multi_action_commit_preserves_legacy_unknown_saved_off(self):
        pedal_id={**IDENTITY,'instance_guid':OTHER}
        proposals=[proposal(),proposal('gas',PEDAL,pedal_id)]
        before=deepcopy(proposals)
        result=C.commit_proposals(self.path,proposals,expected_original=self.original,
                                  inventory=[device(),device(pedal_id)])
        self.assertEqual(result['backup'].read_bytes(),self.original)
        self.assertEqual(C.load_records(self.path),result['records'])
        self.assertEqual(set(result['records']),{'steer','gas'})
        cp=self.read()
        self.assertEqual(cp['collection']['ffb_enabled'],'0');self.assertEqual(cp['collection']['ffb'],'63')
        self.assertEqual(cp['wheelmap']['steer'],'Old wheel|axis:0:0:pos')
        self.assertEqual(cp['wheelmap']['gear1'],'Shifter|btn:6')
        self.assertEqual(cp['collection']['owner_note'],'100% custom')
        self.assertEqual(cp['telemetry']['forza'],'192.0.2.10:8000')
        self.assertEqual(cp['Owner']['MixedCase'],'kept')
        self.assertEqual(proposals,before)

    def test_explicit_legacy_update_and_calibration_are_one_replace(self):
        first=proposal(legacy_binding='New wheel|axis:0:0:pos')
        original_replace=C.os.replace
        with mock.patch.object(C.os,'replace',wraps=original_replace) as replace:
            C.commit_proposals(self.path,[first],expected_original=self.original,inventory=[device()])
        self.assertEqual(replace.call_count,1)
        self.assertEqual(self.read()['wheelmap']['steer'],'New wheel|axis:0:0:pos')
        self.assertEqual(C.load_records(self.path)['steer']['calibration'],STEER)

    def test_failed_replace_preserves_exact_original_and_proposals(self):
        proposals=[proposal(legacy_binding='Replacement|axis:0:0:neg'),proposal('brake',PEDAL)]
        before=deepcopy(proposals)
        with mock.patch.object(C.os,'replace',side_effect=OSError('denied')):
            with self.assertRaises(OSError): C.commit_proposals(self.path,proposals,
                expected_original=self.original,inventory=[device()])
        self.assertEqual(self.path.read_bytes(),self.original)
        self.assertEqual(proposals,before)
        backups=list(self.path.parent.glob('*.bak'))
        self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_bytes(),self.original)
        self.assertFalse(list(self.path.parent.glob('*.tmp')))

    def test_expected_original_and_concurrent_edit_keep_external_bytes(self):
        changed=b'[collection]\nffb_enabled=0\nowner=changed\n'
        self.path.write_bytes(changed)
        with self.assertRaisesRegex(ValueError,'changed while editing'):
            C.commit_proposals(self.path,[proposal()],expected_original=self.original,inventory=[device()])
        self.assertEqual(self.path.read_bytes(),changed)
        self.assertFalse(list(self.path.parent.glob('*.bak')))
        self.path.write_bytes(self.original)
        actual_temp=C.tempfile.NamedTemporaryFile
        def concurrent(*args,**kwargs):
            self.path.write_bytes(changed)
            return actual_temp(*args,**kwargs)
        with mock.patch.object(C.tempfile,'NamedTemporaryFile',side_effect=concurrent):
            with self.assertRaisesRegex(ValueError,'changed before replacement'):
                C.commit_proposals(self.path,[proposal()],expected_original=self.original,inventory=[device()])
        self.assertEqual(self.path.read_bytes(),changed)
        self.assertFalse(list(self.path.parent.glob('*.tmp')))

    def test_missing_ambiguous_axis_loss_or_duplicate_action_writes_nothing(self):
        for proposals,inventory in (([proposal()],[]),([proposal()],[device(),device()]),
                ([proposal()],[device(axes=['YAXIS'])]),([proposal(),proposal()],[device()])):
            with self.subTest(inventory=inventory),self.assertRaises(ValueError):
                C.commit_proposals(self.path,proposals,expected_original=self.original,inventory=inventory)
            self.assertEqual(self.path.read_bytes(),self.original)
        self.assertEqual(list(self.path.parent.iterdir()),[self.path])

    def test_new_file_no_calibration_is_explicit_no_other_defaults(self):
        self.path.unlink()
        result=C.commit_proposals(self.path,[proposal(calibration=None)],expected_original=None,inventory=[device()])
        self.assertIsNone(result['backup'])
        self.assertIsNone(C.load_records(self.path)['steer']['calibration'])
        self.assertEqual(set(self.read().sections()),{'control_preferences','control:steer'})

    def test_unknown_owned_metadata_survives_a_later_save(self):
        initial=proposal();initial['record']['owner_extension']={'note':'keep'}
        C.commit_proposals(self.path,[initial],expected_original=self.original,inventory=[device()])
        cp=self.read();cp['control:steer']['owner_note']='keep this too'
        with self.path.open('w',encoding='utf-8') as f:cp.write(f)
        original=self.path.read_bytes()
        C.commit_proposals(self.path,[proposal(calibration=None)],expected_original=original,inventory=[device()])
        self.assertEqual(C.load_records(self.path)['steer']['owner_extension'],{'note':'keep'})
        self.assertEqual(self.read()['control:steer']['owner_note'],'keep this too')
        self.assertEqual(len(list(self.path.parent.glob('*.bak'))),2)

    def test_future_or_malformed_schema_does_not_migrate_or_write(self):
        malformed=[b'[control_preferences]\nversion=99\n',b'[control:steer]\nrecord={}\n',
                   b'[DEFAULT]\nversion=1\n[control_preferences]\n',
                   b'[control_preferences]\nversion=1\n[control:steer]\nrecord={broken\n']
        for data in malformed:
            self.path.write_bytes(data)
            with self.assertRaises(ValueError):C.load_records(self.path)
            with self.assertRaises(ValueError):C.commit_proposals(self.path,[proposal()],expected_original=data,inventory=[device()])
            self.assertEqual(self.path.read_bytes(),data)
        self.path.write_bytes(self.original)
        self.assertEqual(C.load_records(self.path),{})
        self.assertEqual(self.path.read_bytes(),self.original)


if __name__ == '__main__':
    unittest.main()
