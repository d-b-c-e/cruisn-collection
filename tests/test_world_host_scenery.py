import copy
import argparse
import json
import lzma
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from scenery_c31 import F
from world_host_scenery import camera_center, rotation_matrix, model_counts, project, fast_quads
from world_host_options import add_arguments,configure


class SceneryMathTests(unittest.TestCase):
    def test_against_frozen_actual_mame_arithmetic(self):
        root=Path(__file__).resolve().parents[1]/'fixtures/scenery'
        data=json.loads(lzma.decompress((root/'c31-vectors.json.xz').read_bytes()))
        self.assertEqual(len(data['vectors']),10081)
        for am,ae,bm,be,expected in data['vectors']:
            a,b=F(am,ae),F(bm,be)
            actual=[]
            for value in (a+b,a-b,a*b,-a):actual.extend((value.mantissa,value.exponent))
            integer=F.integer(am)
            actual.extend((a.fix(),integer.mantissa,integer.exponent))
            self.assertEqual(actual,expected,(am,ae,bm,be))

    def test_negative_fix_and_store_are_not_round_to_nearest(self):
        f=F.load(0xffc00000)  # -0.75, floor is -1
        self.assertEqual(f.value(),-0.75)
        self.assertEqual(f.fix(),-1)
        extended=F(255,0)
        self.assertNotEqual(extended.value(),extended.reload().value())
        self.assertEqual(extended.reload(),F.integer(1))


class WorldModelTests(unittest.TestCase):
    def record(self):
        f=lambda x:F.integer(x).store()
        identity=[f(x) for x in (1,0,0,0,1,0,0,0,1)]
        obj=[0]*32
        obj[1:4]=[f(0),f(0),f(1024)]
        obj[4:13]=identity
        obj[16:18]=[0x200,0x40]
        # Four vertices in the accepted screen winding, one polygon.
        xy=lambda x,y:((y&65535)<<16)|(x&65535)
        words=[20,1234,4,xy(-10,-10),0,xy(10,-10),0,xy(10,10),0,xy(-10,10),0,0x100,0x03020100]
        return dict(object_words=obj,camera=[f(0)]*3,view=identity,matrix=identity,
                    camera_space=[f(0),f(0),f(1024),f(256),f(200)],model_words=words,
                    material_words=[0x00100000,0x10001010,0x20],fast=1,end_pc=0x242)

    def test_independent_synthetic_positions_materials_and_backfaces(self):
        r=self.record();rec={64:F.integer(1).store()}
        center=camera_center(r['object_words'],r['camera'],r['view'])
        matrix=rotation_matrix(r['object_words'],r['view'])
        p=project(r,rec,center=center,matrix=matrix)
        self.assertEqual(fast_quads(r,p),[[0x100,0x200,246,189,266,189,266,210,246,210,0,16,4112,4096,0x60]])
        reverse=copy.deepcopy(r);reverse['model_words'][-1]=0x00010203
        self.assertEqual(fast_quads(reverse,p),[])

    def test_two_vertices_per_packed_axis_pair(self):
        r=self.record()
        # Two base vertices, each extended along Y by +20, no ordinary vertices.
        r['model_words']=[20,1234,0x600,0xfff6fff6,20,0xfff6000a,20,0x100,0x01030200]
        self.assertEqual(model_counts(0x600),(2,0,1))
        p=project(r,{64:F.integer(1).store()})
        points=[[F.load(p[i+j]).fix() for j in (0,1,2)] for i in range(0,12,3)]
        self.assertEqual(points,[[246,189,1024],[246,210,1024],[266,189,1024],[266,210,1024]])

    def test_uncaptured_projection_and_unsupported_clipping_fail(self):
        r=self.record()
        with self.assertRaisesRegex(ValueError,'uncaptured'):project(r,{})
        r['end_pc']=0x2e1
        with self.assertRaisesRegex(ValueError,'clipped'):fast_quads(r,[])
        with self.assertRaises(ValueError):model_counts(0)


class HostOptionsTests(unittest.TestCase):
    def test_revision_bounds_and_simulation_exclusions(self):
        parser=argparse.ArgumentParser();add_arguments(parser)
        args=parser.parse_args(['--world-host-scenery','draw','--world-host-first','5900','--world-host-last','6020'])
        with self.assertRaises(ValueError):configure(args,'crusnwld',{'MIDV_GL':'1'})
        with self.assertRaises(ValueError):configure(args,'crusnwld24',{'MIDV_GL':'1','MIDV_WORLD_FAR':'160000'})
        with self.assertRaises(ValueError):configure(args,'crusnwld24',{'MIDV_GL':'1','MIDV_SCENERY':'all'})
        with self.assertRaises(ValueError):configure(args,'crusnwld24',{})
        settings={'MIDV_GL':'1'};configure(args,'crusnwld24',settings)
        self.assertEqual(settings['MIDV_WORLD_HOST_SCENERY'],'2')
        self.assertEqual(settings['MIDV_WORLD_HOST_LAST'],'6020')
        inherited=parser.parse_args([]);inherited.headless=True
        with self.assertRaises(ValueError):configure(inherited,'crusnwld24',settings)
        off=parser.parse_args(['--world-host-scenery','off']);configure(off,'crusnwld24',settings)
        self.assertNotIn('MIDV_WORLD_HOST_LAST',settings)
        unbounded=parser.parse_args(['--world-host-scenery','observe'])
        with self.assertRaises(ValueError):configure(unbounded,'crusnwld24',settings)


if __name__=='__main__':unittest.main()
