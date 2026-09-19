"""Real UI controller with fake inventory/reader; no COM, window or game calls."""
from copy import deepcopy
import configparser
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import control_preferences as P
import control_setup as S

IDENTITY = dict(backend='dinput', product_guid='0006346e-0000-0000-0000-504944564944',
                instance_guid='11111111-2222-3333-4444-555555555555',
                hid_path=r'\\?\HID#FIXTURE', ffb_capable=True)
DEVICE = dict(name='Fixture wheel', identity=IDENTITY, axes=['XAXIS', 'ZAXIS'])
CAL = dict(version=1, kind='steering', left=-1., centre=0., right=1., invert=False, deadzone=0.)


class Reader:
    def __init__(self, owner, device):
        self.owner = owner
        self.device = deepcopy(device)
        self.closed = False
        owner.readers.append(self)
    def sample(self):
        assert not self.closed
        return deepcopy(self.owner.sample)
    def close(self):
        if not self.closed:
            self.closed = True
            self.owner.closes += 1


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'collection.ini'
        self.original = b'[collection]\nffb_enabled=0\nffb=72\nffb_profile=owner@7\ncustom=100%\n[wheelmap]\ngas=Old pedal|axis:1:0:neg\nview1=Wheel|btn:2\n[telemetry]\nforza=192.0.2.8:9000\n'
        self.path.write_bytes(self.original)
        self.devices = [deepcopy(DEVICE)]
        self.readers, self.closes = [], 0
        self.sample = dict(axes={'XAXIS':0., 'ZAXIS':1.}, buttons=(False,)*128)
        self.now, self.frame = 0., 0
        self.session = S.Session(self.path, self.inventory, self.reader, 123,
            supported=lambda _:False, ffb_load=lambda _:dict(mode='steering',identity=None))
        self.addCleanup(self.session.close)

    def inventory(self):
        self.assertFalse(any(not reader.closed for reader in self.readers), 'inventory must not overlap reader ownership')
        return deepcopy(self.devices)
    def reader(self, device, window):
        self.assertEqual(window, 123)
        self.assertFalse(any(not reader.closed for reader in self.readers), 'one reader at a time')
        return Reader(self, device)
    def tick(self, seconds=.1, **kw):
        self.now += seconds
        self.frame += 1
        self.session.tick(self.now, frame=self.frame, **kw)
    def settle(self, value, axis='XAXIS', **kw):
        self.sample['axes'][axis] = value
        for _ in range(6): self.tick(**kw)
    def begin(self, role='steer', axis='XAXIS'):
        self.session.open(role, self.now)
        self.session.activate('device:0')
        self.session.activate('axis:'+axis)
        self.assertEqual(self.session.mode, 'capture')
    def steering(self):
        self.begin()
        for value in (0., -.8, 1., 0.):
            self.settle(value)
            self.session.activate('capture')
        self.assertEqual(self.session.mode, 'review', self.session.error)

    def test_opening_picker_never_enables_force_or_saves(self):
        self.session.open('steer', 0)
        self.assertEqual(self.session.mode, 'devices')
        self.assertFalse(self.readers)
        status=next(row for row in self.session.rows() if row[0]=='status')
        self.assertEqual(status[2],'Update required')
        self.assertIn('Update the collection runtime',status[3])
        self.session.ready_native=True
        status=next(row for row in self.session.rows() if row[0]=='status')
        self.assertEqual(status[2],'Ready for next launch')
        self.assertIn('launch a game to check',status[3])
        self.assertEqual(S.device_label(DEVICE,[DEVICE]),'Fixture wheel')
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_steering_staged_save_preserves_other_roles_off_and_unknown(self):
        self.steering()
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertIn('Centre', next(r[2] for r in self.session.rows() if r[0]=='preview'))
        self.session.activate('save')
        self.assertEqual(self.session.mode, 'closing', self.session.error)
        saved = P.load_records(self.path)['steer']
        self.assertAlmostEqual(saved['calibration']['left'], -.8)
        self.assertEqual(saved['identity']['instance_guid'], IDENTITY['instance_guid'])
        cp=configparser.ConfigParser(interpolation=None); cp.read(self.path,encoding='utf-8')
        self.assertEqual(cp['collection']['ffb_enabled'],'0')
        self.assertEqual(cp['collection']['ffb_profile'],'owner@7')
        self.assertEqual(cp['collection']['custom'],'100%')
        self.assertEqual(cp['wheelmap']['view1'],'Wheel|btn:2')
        self.assertEqual(cp['wheelmap']['gas'],'Old pedal|axis:1:0:neg')
        self.assertEqual(cp['telemetry']['forza'],'192.0.2.8:9000')
        self.assertEqual(self.closes, 1)

    def test_reversed_pedal_and_neutral_handoff(self):
        self.begin('gas','ZAXIS')
        for value in (1.,-1.,1.):
            self.settle(value, 'ZAXIS'); self.session.activate('capture')
        self.assertEqual(self.session.mode,'review',self.session.error)
        self.settle(-1.,'ZAXIS')
        self.assertIn('Full 100%',next(r[2] for r in self.session.rows() if r[0]=='preview'))
        self.session.cancel()
        self.tick(); self.tick()
        self.assertEqual(self.session.mode,'closing')
        self.settle(1.,'ZAXIS',external_held=True)
        self.assertEqual(self.session.mode,'closing')
        self.tick(); self.tick()
        self.assertEqual(self.session.mode,'closed')
        self.assertEqual(self.closes,1)
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_stability_and_other_moving_axis_reject_without_capture(self):
        self.begin()
        self.tick()
        self.session.activate('capture')
        self.assertFalse(self.session.draft.samples)
        for i in range(6):
            self.sample['axes']['XAXIS'] = .05 if i%2 else 0.
            self.tick()
        self.session.activate('capture')
        self.assertIn('still moving',self.session.error)
        self.sample['axes']['ZAXIS'] = -.5
        self.settle(0.)
        self.session.activate('capture')
        self.assertIn('More than one',self.session.error)
        self.assertFalse(self.session.draft.samples)
        self.sample['axes']['ZAXIS'] = 1.
        self.settle(0.); self.session.activate('capture')
        self.assertEqual(set(self.session.draft.samples),{'centre'})

    def test_save_failure_retains_proposal_retry_cancel_and_exact_old_bytes(self):
        self.steering()
        proposal=deepcopy(self.session.proposal)
        with mock.patch.object(P.os,'replace',side_effect=OSError('disk unavailable')):
            self.session.activate('save')
        self.assertEqual(self.session.mode,'save_error')
        self.assertEqual(self.session.proposal,proposal)
        self.assertEqual(self.path.read_bytes(),self.original)
        self.assertTrue({'save','cancel'} <= {r[0] for r in self.session.rows()})
        self.tick()  # The reopened exact reader must deliver a fresh sample.
        self.session.activate('save')
        self.assertIn('steer',P.load_records(self.path))
        self.assertEqual(self.session.mode,'closing')

    def test_disconnect_and_focus_loss_close_reader_keep_file(self):
        for trigger in ('disconnect','focus'):
            with self.subTest(trigger=trigger):
                self.sample = dict(axes={'XAXIS':0.,'ZAXIS':1.},buttons=())
                self.begin()
                self.tick()
                if trigger=='disconnect': self.sample=None
                self.tick(focused=trigger!='focus')
                self.assertIsNone(self.session.reader)
                self.assertEqual(self.session.mode,'closing')
                self.assertEqual(self.path.read_bytes(),self.original)

    def test_timeout_and_window_shutdown_discard(self):
        self.begin(); self.tick()
        self.tick(seconds=91)
        self.assertEqual(self.session.mode,'closing')
        self.session.close(); self.session.close()
        self.assertEqual(self.closes,1)
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_missing_ambiguous_identity_never_opens_another_reader(self):
        P.commit_proposals(self.path,[P.make_proposal('steer',IDENTITY,'XAXIS',CAL)],expected_original=self.original,inventory=self.devices)
        for devices in ([],[deepcopy(DEVICE),deepcopy(DEVICE)]):
            self.devices=devices
            self.session.open('steer',0)
            self.assertIsNone(self.session.reader)
            self.assertIn('Saved device',self.session.error)

    def test_staged_invert_deadzone_only_explicit_and_no_draw_write(self):
        self.steering()
        self.session.activate('invert');self.session.activate('deadzone:0.01')
        self.assertTrue(self.session.proposal['record']['calibration']['invert'])
        self.assertEqual(self.session.proposal['record']['calibration']['deadzone'],.01)
        self.assertEqual(self.session.proposal['record']['identity']['display_name'],'Fixture wheel')
        for _ in range(5): self.session.rows()
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_concurrent_file_edit_rejected_without_overwrite(self):
        self.steering()
        external=self.original+b'\n[other]\nowner=changed\n'
        self.path.write_bytes(external)
        self.session.activate('save')
        self.assertEqual(self.session.mode,'save_error')
        self.assertEqual(self.path.read_bytes(),external)

    def test_ffb_dropdown_follow_explicit_and_failed_save_keep_off(self):
        self.session.open('ffb',0)
        self.assertTrue({'follow','ffb:0','cancel'} <= {r[0] for r in self.session.rows()})
        self.session.activate('ffb:0')
        self.assertEqual(self.path.read_bytes(),self.original)
        calls=[]
        def save(path,mode,identity,**kw):
            calls.append((mode,identity,kw))
            raise OSError('locked')
        self.session.ffb_save=save
        self.session.activate('save_ffb')
        self.assertEqual(self.session.mode,'save_error')
        self.assertEqual(calls[0][0],'explicit')
        self.assertEqual(calls[0][2]['expected_original'],self.original)
        self.assertEqual(self.path.read_bytes(),self.original)
        self.assertFalse(self.readers)

    def test_output_picker_rejects_missing_path_and_same_name_twins_stay_distinct(self):
        other=deepcopy(DEVICE); other['identity']['instance_guid']='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
        other['identity'].pop('hid_path')
        self.devices.append(other)
        self.session.open('ffb',0)
        self.assertNotIn('ffb:1',{r[0] for r in self.session.rows()})
        self.session.activate('ffb:1')
        self.assertIn('no verified output path',self.session.error)
        self.session.open('steer',0)
        labels=[r[1] for r in self.session.rows() if r[0].startswith('device:')]
        self.assertEqual(len(set(labels)),2)
        self.assertEqual(labels,['Fixture wheel [11111111]','Fixture wheel [aaaaaaaa]'])

    def test_clear_is_explicit_proposal_and_failure_retained(self):
        self.session.open('gas',0)
        self.session.activate('clear')
        self.assertEqual(self.path.read_bytes(),self.original)
        calls=[]
        def clear(path,role,**kw):
            calls.append(role);raise OSError('locked')
        self.session.clear=clear
        self.session.activate('save_clear')
        self.assertEqual(calls,['gas'])
        self.assertEqual(self.session.mode,'save_error')
        self.assertTrue({'save_clear','cancel'} <= {r[0] for r in self.session.rows()})
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_preview_vectors_and_invalid_sample(self):
        self.assertIn('Left 100%',S.preview_text('steer',-1.,CAL))
        self.assertIn('Right 100%',S.preview_text('steer',1.,CAL))
        self.assertIn('Centre',S.preview_text('steer',0.,CAL))
        self.assertIn('calibration needed',S.preview_text('gas',1.,None))
        self.begin(); self.sample['axes']['XAXIS']=float('nan');self.tick()
        self.assertIsNone(self.session.reader)
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_saved_and_failed_save_keep_reader_for_release_and_retry(self):
        self.steering()
        with mock.patch.object(P.os,'replace',side_effect=OSError('locked')):
            self.session.activate('save')
        self.assertIsNotNone(self.session.reader)
        self.session.activate('save')
        self.assertEqual(self.path.read_bytes(),self.original)
        self.settle(.9)
        self.session.activate('save')
        self.assertEqual(self.path.read_bytes(),self.original)
        self.settle(0.)
        self.session.activate('save')
        self.assertEqual(self.session.mode,'closing')
        self.assertIsNotNone(self.session.reader)
        self.settle(.9)
        self.assertEqual(self.session.mode,'closing')
        self.settle(0.,external_held=True)
        self.assertEqual(self.session.mode,'closing')
        self.tick();self.tick()
        self.assertEqual(self.session.mode,'closed')
        self.assertTrue(all(reader.closed for reader in self.readers))

    def test_disconnection_after_saved_change_does_not_claim_rollback(self):
        self.steering();self.session.activate('save')
        saved=self.path.read_bytes()
        self.sample=None;self.tick()
        self.assertIn('Saved change retained',self.session.message)
        self.assertEqual(self.path.read_bytes(),saved)

    def test_bad_endpoints_can_restart_without_changing_saved_assignment(self):
        self.begin()
        for value in (0.,0.,0.,0.):
            self.settle(value);self.session.activate('capture')
        self.assertEqual(self.session.mode,'capture')
        self.assertTrue(self.session.error)
        self.session.activate('calibrate')
        self.assertFalse(self.session.draft.samples)
        self.assertEqual(self.session.mode,'capture')
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_draw_current_missing_ffb_identity_and_role_repair_independent(self):
        missing=deepcopy(IDENTITY);missing['instance_guid']='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
        self.session.ffb_load=lambda _:dict(mode='explicit',identity=missing)
        self.session.open('ffb',0)
        self.assertIn('missing',next(row[2] for row in self.session.rows() if row[0]=='current'))
        def broken_ffb(_): raise ValueError('invalid FFB configuration')
        self.session.ffb_load=broken_ffb
        self.session.open('gas',0)
        self.assertEqual(self.session.mode,'devices')
        self.session.open('ffb',0)
        self.assertEqual(self.session.mode,'ffb')
        self.assertIn('Invalid saved choice',next(row[2] for row in self.session.rows() if row[0]=='current'))
        self.assertTrue({'follow','ffb:0'} <= {row[0] for row in self.session.rows()})
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_actual_launcher_rows_and_modal_layout_use_same_scrolling_hits(self):
        from test_graphics_options import import_shell_module
        import settings_view as V
        shell=import_shell_module('collection')
        with mock.patch.object(shell,'CFG',str(self.path)):
            state=shell.load_config()
        controls=shell.settings_rows('controls',state,False,'fixture')
        self.assertTrue({'bind_steer','bind_gas','bind_brake','wizard'} <= {r[0] for r in controls})
        self.assertIn('ffb_device',{r[0] for r in shell.settings_rows('ffb',state,False,'fixture')})
        self.steering()
        rows=self.session.rows()
        self.assertTrue({'preview','invert','deadzone','save','cancel'} <= {r[0] for r in rows})
        self.assertEqual(len(rows),len({r[0] for r in rows}))
        # Run the real layout with a recording surface, no GL context/window.
        class Surface:
            def __init__(self,w,h):
                self.w,self.h=w,h
                self.ctx=mock.Mock()
                self.bg=self.title=type('Texture',(),dict(width=100,height=30))()
                self.calls=[]
            def rect(self,*args,**kwargs):pass
            def center_text(self,text,px,y,*args):self.calls.append((text,y))
            def text_at(self,text,px,x,y,*args,**kwargs):self.calls.append((text,y))
            def footer_tex(self,text):
                self.calls.append((text,self.h*.92));return self.title
        with mock.patch.object(shell.moderngl,'BLEND',1,create=True):
            for w,h in ((1280,720),(1920,1080)):
                surface=Surface(w,h)
                for selected in (1,len(rows)-1):
                    shell.Shell.draw_settings(surface,selected,'CONTROL SETUP',[(r[1],r[2]) for r in rows],rows[selected][3],0)
                    first=max(0,selected-8)
                    for offset in range(min(8,len(rows)-1-first)):
                        hit=V.hit_row(w,h,w*.5,h*(.401+.048*offset),selected,len(rows))
                        self.assertEqual(hit,first+offset+1)
                self.assertFalse(any('TAB  PAGE' in text for text,_ in surface.calls))
                self.assertTrue(all(0 <= y <= h for _,y in surface.calls))
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_actual_text_bounds_and_row_collisions_at_720p_and_4k(self):
        from test_graphics_options import import_shell_module
        shell=import_shell_module('collection')
        from render_settings_fixture import Fixture
        cases=[]
        def remember(name):
            rows=self.session.rows()
            cases.append((name,'FFB DEVICE' if self.session.role=='ffb' else 'CONTROL SETUP',
                          rows,self.session.selected,self.session.error))
        self.devices[0]['name']='Long fixture wheel name with duplicate display product'
        self.session.open('steer',0);remember('devices')
        self.session.activate('device:0');remember('axes')
        self.session.activate('axis:XAXIS');remember('capture')
        self.session.close();self.steering();remember('review')
        self.session.activate('clear');remember('clear')
        self.session.close();self.session.open('ffb',self.now);remember('ffb-devices')
        self.session.activate('ffb:0');remember('ffb-review')
        self.session.ffb_save=mock.Mock(side_effect=OSError('Fixture save unavailable; the last saved settings were retained.'))
        self.session.activate('save_ffb');remember('retry')
        self.session.cancel();remember('release')
        report=[]
        output=Path(os.environ['CRUISN_CONTROL_LAYOUT_OUTPUT']) if os.environ.get('CRUISN_CONTROL_LAYOUT_OUTPUT') else None
        if output:output.mkdir(parents=True,exist_ok=True)
        with mock.patch.object(shell.moderngl,'BLEND',1,create=True):
            for width,height in ((1280,720),(3840,2160)):
                for name,title,rows,selected,error in cases:
                    fixture=Fixture(width,height)
                    fixture.draw_settings(selected,title,[(r[1],r[2]) for r in rows],rows[selected][3],0,notice=error)
                    outside=[r for r in fixture.bounds if r['x']<0 or r['x']+r['width']>width or r['y']+r['height']>height]
                    collisions=[]
                    for i,a in enumerate(fixture.bounds):
                        for b in fixture.bounds[i+1:]:
                            if a['y']==b['y'] and a['x']<b['x']+b['width'] and b['x']<a['x']+a['width']:
                                collisions.append((a['text'],b['text']))
                    self.assertFalse(outside,(name,width,outside))
                    self.assertFalse(collisions,(name,width,collisions))
                    image=f'{width}-{name}.png'
                    report.append(dict(image=image,width=width,height=height,outside=outside,collisions=collisions))
                    if output:fixture.canvas.convert('RGB').save(output/image)
        if output:
            (output/'report.json').write_text(json.dumps(dict(scope='Actual CPU settings layout; no GPU, devices or input',images=report,passed=True),indent=2)+'\n',encoding='utf-8')

    @unittest.skipUnless(importlib.util.find_spec('control_launch'), 'Owner control_launch integration commit required')
    def test_owner_helpers_clear_legacy_rebind_and_ffb_scoped_atomic_roundtrip(self):
        import control_launch as launch
        from test_graphics_options import import_shell_module
        shell=import_shell_module('collection')
        self.steering();self.session.activate('save');self.session.close()
        saved=self.path.read_bytes()
        self.session.clear=S.clear_role
        self.session.open('steer',self.now);self.session.activate('clear')
        self.assertEqual(self.path.read_bytes(),saved)
        self.session.activate('save_clear');self.session.close()
        self.assertNotIn('steer',P.load_records(self.path))
        cp=configparser.ConfigParser(interpolation=None);cp.read(self.path,encoding='utf-8')
        self.assertEqual(cp['control_unbound']['steer'],'1')
        self.assertEqual(cp['wheelmap']['gas'],'Old pedal|axis:1:0:neg')
        self.steering();self.session.activate('save');self.session.close()
        with mock.patch.object(shell,'CFG',str(self.path)):
            shell.save_wheelmap({'steer':'Legacy wheel|axis:0:0:pos'})
        self.assertNotIn('steer',P.load_records(self.path))
        cp=configparser.ConfigParser(interpolation=None);cp.read(self.path,encoding='utf-8')
        self.assertNotIn('steer',cp['control_unbound'])
        self.assertEqual(cp['wheelmap']['steer'],'Legacy wheel|axis:0:0:pos')
        self.session.ffb_load=S.load_ffb
        self.session.open('ffb',self.now);self.session.activate('ffb:0');self.session.activate('save_ffb')
        self.assertEqual(launch.load_ffb_selection(self.path)['mode'],'explicit')
        self.session.close()
        self.session.open('ffb',self.now);self.session.activate('follow');self.session.activate('save_ffb')
        self.assertEqual(launch.load_ffb_selection(self.path),dict(mode='steering',identity=None))
        cp.read(self.path,encoding='utf-8')
        self.assertEqual(cp['collection']['ffb_enabled'],'0')
        self.assertEqual(cp['collection']['ffb_profile'],'owner@7')
        self.assertEqual(cp['telemetry']['forza'],'192.0.2.8:9000')


if __name__=='__main__':unittest.main()
