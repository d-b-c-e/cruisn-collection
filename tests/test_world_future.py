import argparse
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from world_future_sections import future,section_definitions,material_operands
from world_host_options import add_arguments,configure


class FutureSectionTests(unittest.TestCase):
    def test_world25_freezes_supported_options_but_rejects_unverified_roads(self):
        parser=argparse.ArgumentParser();add_arguments(parser)
        args=parser.parse_args(['--world-host-scenery','draw','--world-host-first','1800',
            '--world-host-last','5990','--world-host-source','future','--world-host-far','240000'])
        settings={'MIDV_GL':'1'}
        original=configure(args,'crusnwld',settings)
        self.assertEqual(configure(parser.parse_args([]),'crusnwld',settings),original)
        self.assertNotIn('MIDV_WORLD_HOST_ROADS',settings)
        for rom in ('crusnusa','offroadc','crusnexo','crusnwld23'):
            with self.assertRaises(ValueError):configure(args,rom,dict(settings))
        settings['MIDV_WORLD_HOST_ROADS']='1'
        with self.assertRaisesRegex(ValueError,'World 2.4'):configure(parser.parse_args([]),'crusnwld',settings)

    def test_world25_frontier_uses_its_own_bindings(self):
        m=self.memory();expected=future(m.__getitem__)
        for old,new in ((0xd575,0xd56f),(0xd5a5,0xd59f),(0xd5a1,0xd59b)):
            m[new]=m.pop(old)
        self.assertEqual(future(m.__getitem__,revision=25),expected)
        m[0xd59f]=1;m[0xd59b]=0xc20008
        self.assertEqual(future(m.__getitem__,revision=25)['skipped_allocated'],1)
        m[0xd56f]=0
        self.assertEqual(future(m.__getitem__,revision=25)['definitions'],[])
        with self.assertRaises(ValueError):future(m.__getitem__,revision=23)

    def test_road_codec_is_explicit_and_recordings_keep_their_choice(self):
        parser=argparse.ArgumentParser();add_arguments(parser)
        settings={'MIDV_GL':'1'}
        with self.assertRaises(ValueError):configure(parser.parse_args(['--world-host-roads','on']),'crusnwld24',settings)
        base=['--world-host-scenery','draw','--world-host-first','1','--world-host-last','2']
        configure(parser.parse_args(base),'crusnwld24',settings)
        configure(parser.parse_args([]),'crusnwld24',settings)
        self.assertNotIn('MIDV_WORLD_HOST_ROADS',settings)
        for option,value in [('on','1'),('off','0')]:
            configure(parser.parse_args(base+['--world-host-roads',option]),'crusnwld24',settings)
            self.assertEqual(settings['MIDV_WORLD_HOST_ROADS'],value)
            self.assertEqual(configure(parser.parse_args([]),'crusnwld24',settings)['roads'],option)
        settings['MIDV_WORLD_HOST_ROADS']='2'
        with self.assertRaises(ValueError):configure(parser.parse_args([]),'crusnwld24',settings)
        configure(parser.parse_args(['--world-host-scenery','off']),'crusnwld24',settings)
        self.assertNotIn('MIDV_WORLD_HOST_ROADS',settings)

    def test_host_layer_trial_freezes_without_changing_old_recordings(self):
        parser=argparse.ArgumentParser();add_arguments(parser)
        for label,value in (('legacy','0'),('coverage','1'),('split','2'),('both','3')):
            settings={'MIDV_GL':'1'}
            with self.assertRaises(ValueError):configure(parser.parse_args(['--world-host-layer',label]),'crusnwld24',settings)
            args=parser.parse_args(['--world-host-scenery','draw','--world-host-first','1',
                '--world-host-last','2','--world-host-layer',label])
            configure(args,'crusnwld24',settings)
            self.assertEqual(settings['MIDV_WORLD_HOST_LAYER'],value)
            self.assertEqual(configure(parser.parse_args([]),'crusnwld24',settings)['layer'],label)
            configure(parser.parse_args(['--world-host-scenery','off']),'crusnwld24',settings)
            self.assertNotIn('MIDV_WORLD_HOST_LAYER',settings)
        settings={'MIDV_GL':'1'}
        configure(parser.parse_args(['--world-host-scenery','draw','--world-host-first','1','--world-host-last','2']),'crusnwld24',settings)
        configure(parser.parse_args([]),'crusnwld24',settings)
        self.assertNotIn('MIDV_WORLD_HOST_LAYER',settings)
        settings['MIDV_WORLD_HOST_LAYER']='4'
        with self.assertRaises(ValueError):configure(parser.parse_args([]),'crusnwld24',settings)

    def test_future_source_is_explicit_frozen_and_removed_when_disabled(self):
        parser=argparse.ArgumentParser();add_arguments(parser)
        settings={'MIDV_GL':'1'}
        with self.assertRaises(ValueError):configure(parser.parse_args(['--world-host-source','future']),'crusnwld24',settings)
        args=parser.parse_args(['--world-host-scenery','draw','--world-host-first','1800','--world-host-last','9260',
            '--world-host-source','future','--world-host-log','summary'])
        configure(args,'crusnwld24',settings)
        self.assertEqual(settings['MIDV_WORLD_HOST_FUTURE'],'1')
        self.assertEqual(configure(parser.parse_args([]),'crusnwld24',settings)['source'],'future')
        configure(parser.parse_args(['--world-host-scenery','off']),'crusnwld24',settings)
        self.assertNotIn('MIDV_WORLD_HOST_FUTURE',settings)
        configure(parser.parse_args(['--world-host-scenery','observe','--world-host-first','1','--world-host-last','2']),'crusnwld24',settings)
        self.assertNotIn('MIDV_WORLD_HOST_FUTURE',settings)

    def memory(self):
        m={0xd575:0xc10000,0xd5a5:0,0xd5a1:0}
        values=[8,0,0,0,0,0xc20000,0xc20020,0xc20030,1,2,3,0]
        m.update({0xc10000+i:v for i,v in enumerate(values)})
        m[0xc1000c]=0xffffffff
        for p,n in ((0xc20000,2),(0xc20020,1),(0xc20030,1)):
            m[p]=0;m[p+1]=n
            for i in range(n):m.update({p+2+6*i+k:v for k,v in enumerate([0xc00002,1,2,3,0x80000000,0xfff00000])})
        return m

    def test_all_lists_offsets_end_marker_and_partial_handover(self):
        m=self.memory();before=dict(m)
        r=future(m.__getitem__)
        self.assertEqual(len(r['definitions']),4);self.assertEqual(m,before)
        self.assertEqual(r['stop'],dict(section=0xc1000c,reason='end marker'))
        self.assertEqual([a['section_flags'] for a in r['definitions']],[8,8,8,0])
        m[0xd5a5]=1;m[0xd5a1]=0xc20008
        r=future(m.__getitem__);self.assertEqual([a['source'] for a in r['definitions']],[0xc20008,0xc20022,0xc20032])
        m[0xd5a5]=2;m[0xd5a1]=0xc20028
        r=future(m.__getitem__);self.assertEqual([a['source'] for a in r['definitions']],[0xc20032])
        m[0xd5a1]=0xc20023
        with self.assertRaises(ValueError):future(m.__getitem__)

    def test_invalid_pointer_and_signed_indices_do_not_read_io(self):
        m=self.memory();m[0xc10005]=0x993000
        with self.assertRaises(ValueError):section_definitions(m.__getitem__,0xc10000)
        m.update({0xc00000:0xffffffff,0xc00001:0,0x4151:0x1000,0x4150:0x2000})
        with self.assertRaises(ValueError):material_operands(m.__getitem__,[0xc00002,0,0,0,0,0xfff00000])
        m[0xd5a5]=3
        with self.assertRaises(ValueError):future(m.__getitem__)


if __name__=='__main__':unittest.main()
