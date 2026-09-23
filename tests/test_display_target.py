import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from display_target import choose,choose_size,parse_size,verify_completed_size,apply_window_target
import argparse


class CaptureDisplayTests(unittest.TestCase):
    def test_zeus_monitor_selection_preserves_small_owner_and_recorded_command(self):
        target=choose_size((3840,2160),[dict(device='4k',primary=True,size=[3840,2160])])
        command=['vunit','crusnexo','-resolution','1920x1080','-screen','old',
                 '-nowindow','-maximize','-nomaximize','-playback','session.inp']
        original=list(command)
        actual=apply_window_target(command,target,zeus_overlay=True)
        self.assertEqual(command,original)
        self.assertEqual(actual[actual.index('-screen')+1],'4k')
        self.assertEqual(actual[actual.index('-resolution')+1],'auto')
        self.assertEqual(actual[-2:],['-window','-nomaximize'])
        self.assertNotIn('-maximize',actual);self.assertNotIn('-nowindow',actual)
        self.assertEqual(actual[actual.index('-playback')+1],'session.inp')

    def test_vunit_and_native_controls_keep_requested_presentation_size(self):
        target=choose_size((3840,2160),[dict(device='4k',primary=True,size=[3840,2160])])
        for rom in ('crusnusa','crusnwld','offroadc','crusnexo'):
            with self.subTest(rom=rom):
                actual=apply_window_target(['vunit',rom,'-window','-nomaximize'],target)
                self.assertEqual(actual[actual.index('-resolution')+1],'3840x2160')
                self.assertIn('-maximize',actual);self.assertNotIn('-nomaximize',actual)

    def test_explicit_capture_size_is_validated_and_selects_an_actual_display(self):
        self.assertEqual(parse_size('3840:2160'),(3840,2160))
        for text in ('3840x2160','1:1','1920:1080:60','-1920:1080'):
            with self.assertRaises(argparse.ArgumentTypeError):parse_size(text)
        displays=[dict(device='4k',primary=False,size=[3840,2160]),dict(device='main',primary=True,size=[1920,1080])]
        self.assertEqual(choose_size((3840,2160),displays)['selected']['device'],'4k')
        with self.assertRaises(ValueError):choose_size((2560,1440),displays)

    def test_explicit_zeus_size_can_select_center_panel_of_exact_triple(self):
        merged=[dict(device='surround',primary=True,size=[7680,1440])]
        target=choose_size((2560,1440),merged,allow_merged_triple=True)
        self.assertTrue(target['merged_center_panel'])
        self.assertEqual(target['selected']['device'],'surround')
        with self.assertRaises(ValueError):choose_size((2560,1440),merged)
        for width,height in ((5120,1440),(7680,2160),(8000,1440)):
            with self.subTest(width=width,height=height):
                with self.assertRaises(ValueError):choose_size(
                    (2560,1440),[dict(device='other',primary=True,size=[width,height])],
                    allow_merged_triple=True)

    def test_4k_reference_cannot_silently_choose_a_1080p_monitor(self):
        reference={5400:{'size':[3840,2160]},5401:{'size':[3840,2160]}}
        available=[{'device':'secondary','primary':False,'size':[1920,1080]},
                   {'device':'primary','primary':True,'size':[3840,2160]}]
        self.assertEqual(choose(reference,available)['selected']['device'],'primary')
        with self.assertRaisesRegex(ValueError,'No display matches'):choose(reference,available[:1])

    def test_variable_reference_size_fails_before_launch(self):
        with self.assertRaisesRegex(ValueError,'fixed presentation size'):
            choose({1:{'size':[1920,1080]},2:{'size':[3840,2160]}},[])

    def test_monitor_selection_does_not_certify_completed_capture_size(self):
        good={5064:{'size':[3840,2160]},5065:{'size':[3840,2160]}}
        self.assertEqual(verify_completed_size((3840,2160),good),
                         dict(requested_size=[3840,2160],frames=2,passed=True))
        for actual in ({5064:{'size':[3440,1440]}},
                       {**good,5066:{'size':[3440,1440]}}):
            with self.assertRaisesRegex(ValueError,'Completed Zeus captures differ'):
                verify_completed_size((3840,2160),actual)
        with self.assertRaisesRegex(ValueError,'No completed Zeus captures'):
            verify_completed_size((3840,2160),{})
