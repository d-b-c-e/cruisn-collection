import argparse
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from usa_host_options import add_arguments,configure

class FarCoverageOptionsTests(unittest.TestCase):
    def options(self):
        parser=argparse.ArgumentParser();add_arguments(parser)
        args=parser.parse_args(['--usa-host-scenery','draw','--usa-host-first','5800',
            '--usa-host-last','5900','--usa-host-far','240000','--usa-host-source','future',
            '--usa-host-far-coverage','on'])
        args.candidate='private-candidate';return args

    def test_explicit_gate_and_recorded_replay(self):
        for rom in ('crusnusa',):
            settings={'MIDV_GL':'1','MIDV_FFB':'0'};args=self.options()
            self.assertEqual(configure(args,rom,settings)['far_coverage'],'on')
            self.assertEqual(settings['MIDV_USA_HOST_FAR_COVERAGE'],'1')
            parser=argparse.ArgumentParser();add_arguments(parser);inherited=parser.parse_args([])
            inherited.candidate=args.candidate
            self.assertEqual(configure(inherited,rom,settings)['far_coverage'],'on')
            args.usa_host_far_coverage='off';configure(args,rom,settings)
            self.assertEqual(settings['MIDV_USA_HOST_FAR_COVERAGE'],'0')
            args.usa_host_far_coverage=None;configure(args,rom,settings)
            self.assertNotIn('MIDV_USA_HOST_FAR_COVERAGE',settings)

    def test_missing_requirements_rejected(self):
        for key,value in [('candidate',None),('usa_host_far',160000),
                ('usa_host_source','pending'),('usa_host_scenery','observe')]:
            with self.subTest(key=key):
                args=self.options();setattr(args,key,value)
                with self.assertRaises(ValueError):configure(args,'crusnusa',{'MIDV_GL':'1','MIDV_FFB':'0'})
        for force in ('1',''):
            with self.assertRaises(ValueError):configure(self.options(),'crusnusa',{'MIDV_GL':'1','MIDV_FFB':force})
        with self.assertRaises(ValueError):configure(self.options(),'offroadc',{'MIDV_GL':'1','MIDV_FFB':'0'})
        parser=argparse.ArgumentParser();add_arguments(parser)
        with self.assertRaises(ValueError):configure(parser.parse_args([]),'crusnusa',{'MIDV_USA_HOST_FAR_COVERAGE':'1'})
