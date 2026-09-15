import argparse
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from world_host_options import add_arguments,configure

class FarCoverageOptionsTests(unittest.TestCase):
    def options(self):
        parser=argparse.ArgumentParser();add_arguments(parser)
        args=parser.parse_args(['--world-host-scenery','draw','--world-host-first','5800',
            '--world-host-last','5900','--world-host-far','240000','--world-host-source','future',
            '--world-host-far-coverage','on'])
        args.candidate='private-candidate';return args

    def test_explicit_gate_and_recorded_replay(self):
        for rom in ('crusnwld24','crusnwld'):
            settings={'MIDV_GL':'1','MIDV_FFB':'0'};args=self.options()
            self.assertEqual(configure(args,rom,settings)['far_coverage'],'on')
            self.assertEqual(settings['MIDV_WORLD_HOST_FAR_COVERAGE'],'1')
            parser=argparse.ArgumentParser();add_arguments(parser);inherited=parser.parse_args([])
            inherited.candidate=args.candidate
            self.assertEqual(configure(inherited,rom,settings)['far_coverage'],'on')
            args.world_host_far_coverage='off';configure(args,rom,settings)
            self.assertEqual(settings['MIDV_WORLD_HOST_FAR_COVERAGE'],'0')
            args.world_host_far_coverage=None;configure(args,rom,settings)
            self.assertNotIn('MIDV_WORLD_HOST_FAR_COVERAGE',settings)

    def test_missing_requirements_rejected(self):
        for key,value in [('candidate',None),('world_host_far',160000),
                ('world_host_source','pending'),('world_host_scenery','observe')]:
            with self.subTest(key=key):
                args=self.options();setattr(args,key,value)
                with self.assertRaises(ValueError):configure(args,'crusnwld',{'MIDV_GL':'1','MIDV_FFB':'0'})
        for force in ('1',''):
            with self.assertRaises(ValueError):configure(self.options(),'crusnwld',{'MIDV_GL':'1','MIDV_FFB':force})
        with self.assertRaises(ValueError):configure(self.options(),'offroadc',{'MIDV_GL':'1','MIDV_FFB':'0'})
        parser=argparse.ArgumentParser();add_arguments(parser)
        with self.assertRaises(ValueError):configure(parser.parse_args([]),'crusnwld',{'MIDV_WORLD_HOST_FAR_COVERAGE':'1'})
