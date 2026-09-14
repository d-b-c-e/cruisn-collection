import argparse
import csv
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_scene_options as options
from exotica_composition import filtered_geometry,endpoint_geometry
from zeus_host_materials import verify_live


class Composition(unittest.TestCase):
    def test_endpoint_restrictions_keep_depth_test_and_materials(self):
        a=bytearray(260);b=bytearray(a)
        for index,value in [(7,247),(8,8),(9,18),(10,2047)]:struct.pack_into('<I',b,index*4,value)
        endpoint_geometry(a,b)
        for offset in [0,8,36,44,68,259]:
            bad=bytearray(b);bad[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(ValueError):endpoint_geometry(a,bad)
        bad=bytearray(b);bad[36]^=8
        with self.assertRaises(ValueError):endpoint_geometry(a,bad)

    def test_candidate_gate_and_required_paths(self):
        p=argparse.ArgumentParser();p.add_argument('--candidate');options.add_arguments(p)
        base=['--candidate','x.exe','--exotica-host-scene','observe','--exotica-host-first','5000','--exotica-host-last','5002',
              '--exotica-host-fence','observe','--exotica-host-materials','observe','--exotica-host-material-pages','written',
              '--exotica-host-active','draw','--exotica-host-future','draw']
        with self.assertRaisesRegex(ValueError,'no active'):options.configure(p.parse_args(base),'crusnexo',{})
        args=p.parse_args(base+['--exotica-host-compose','margins']);settings={}
        trial=options.configure(args,'crusnexo',settings);self.assertTrue(trial['compose']);self.assertEqual(settings['MIDZ_HOST_COMPOSE'],'1')
        settings.update(MIDZ_GL='1',MIDZ_DEPTH_MIRROR='2',MIDZ_DEPTH_FIRST='2',MIDZ_DEPTH_LAST='5003')
        with self.assertRaisesRegex(ValueError,'completion drawing'):options.validate_runtime(trial,args,settings)
        args.exotica_host_waiting='observe';args.exotica_host_handover='draw';options.validate_runtime(trial,args,settings)
        args.candidate=None
        with self.assertRaisesRegex(ValueError,'candidate'):options.configure(args,'crusnexo',settings)
        args=p.parse_args(base+['--exotica-host-compose','margins']);args.exotica_host_material_pages='scan'
        with self.assertRaisesRegex(ValueError,'tracked'):options.configure(args,'crusnexo',{})

    def test_three_ordered_material_stages(self):
        columns=('scene','frame','generation','pages','palettes','bytes','hash')
        scenes=[dict(scene='12',frame='5000'),dict(scene='13',frame='5001')]
        rows=[dict(zip(columns,map(str,(12+i//3,5000+i//3,i+1,0,0,96,'0000000000000009')))) for i in range(6)]
        text='MIDZ_HOST_MATERIALS_RESULT queued=6 hash=0000000000000009\nMIDZ_HOST_MATERIALS_GPU_RESULT complete=1 received=6 snapshots=0 hash=0000000000000009\n'
        with tempfile.TemporaryDirectory() as temp:
            def run(values):
                for name in ('exotica-host-materials.csv','exotica-host-materials-gpu.csv'):
                    with (Path(temp)/name).open('w',newline='') as f:
                        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(values)
                return verify_live(temp,scenes,[],text,active=True,waiting=True,compose=True)
            self.assertTrue(run(rows)['passed'])
            bad=[dict(r) for r in rows];bad[1]['hash']='000000000000000a'
            with self.assertRaisesRegex(ValueError,'proposal'):run(bad)
            bad=[dict(r) for r in rows];bad[1].update(pages='1',bytes='4196')
            with self.assertRaisesRegex(ValueError,'proposal'):run(bad)
            bad=[dict(r) for r in rows];bad[2].update(pages='1',bytes='4196');self.assertTrue(run(bad)['passed'])
            with self.assertRaisesRegex(ValueError,'contract'):run([rows[0],rows[2],rows[1],*rows[3:]])
            with self.assertRaisesRegex(ValueError,'drain'):run(rows[:-1])

    def test_independent_overlap_preserves_order_and_rejects_conflicts(self):
        wave=bytes(16777216);state=[0]*17;state[0]=5000;state[1]=3;state[4]=16;state[9]=8
        vertices=[0.,0.,0.,0.,0.,1.]*8;q=struct.pack('<17I48f',*state,*vertices)
        a=(0xbbb5,0x1000,0,0,0,0,0,0,0,0,1);b=(*a[:1],0x1100,*a[2:9],1,1)
        active=struct.pack('<22I',*a,*b);w=(0xa01000,0xa02000,*a[2:]);waiting=struct.pack('<11I',*w)
        owner=struct.pack('<6Q',1,w[0],w[1],a[1],1,2)
        expected=struct.pack('<11I',*b[:9],0,1)
        result=filtered_geometry(active,q+q,waiting,q,owner,wave,wave)
        self.assertEqual(result,(expected,q,1,1))
        changed=bytearray(wave);changed[0]=1
        with self.assertRaises(ValueError):filtered_geometry(active,q+q,waiting,q,owner,wave,changed)
        with self.assertRaisesRegex(ValueError,'identity'):filtered_geometry(active,q+q,waiting,q,owner+owner,wave,wave)
        with self.assertRaisesRegex(ValueError,'missing'):filtered_geometry(active,q+q,waiting,q,b'',wave,wave)
        with self.assertRaisesRegex(ValueError,'render'):filtered_geometry(active,q+q,waiting,q[:-1]+b'\x01',owner,wave,wave)
        with self.assertRaisesRegex(ValueError,'orphaned'):filtered_geometry(active,q+q+q,waiting,q,owner,wave,wave)
