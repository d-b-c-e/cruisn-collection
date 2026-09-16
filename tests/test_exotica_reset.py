from pathlib import Path
import struct,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_bootstrap as b
import exotica_reset as r

class ResetTests(unittest.TestCase):
    def fixture(self,root):
        base=112061;tail=base+1200*31
        pool=[0x31534258,1,7385,7385,base,len(b.CODE),1201,0xbbc9,0xbbd5,tail,tail,0,0xffffffff,base,1200,0]
        pool+=[v for pair in b.CODE for v in pair]+[base+(i+1)*31 for i in range(1200)]+[0]
        (root/'exotica-reset-1-bootstrap.bin').write_bytes(struct.pack('<'+'I'*len(pool),*pool))
        scene=[0x31534358,1,7386,7385,0x67f6,0xff2,0xffffffff,0xffffffff,0x67f5,0x15200ff2,0x681f,0x082fbbb5,0x6835,0x082fbbb9,501,0]
        (root/'exotica-reset-1-scene.bin').write_bytes(struct.pack('<16I',*scene))
        (root/'session-actions.csv').write_text('frame,action\n6000,soft_reset\n',encoding='utf-8')
        (root/'session-action-events.csv').write_text('id,event,frame,time\n1,request,6000,105\n1,complete,6000,105\n',encoding='utf-8')
        lines=['MIDZ_RESET_QUEUED index=1 frame=5999 scene=500 generation=1500 hash=0123456789abcdef epoch=7',
            'MIDZ_RESET_GPU index=1 frame=5999 scene=500 generation=1500 hash=0123456789abcdef',
            f'MIDZ_RESET_READY index=1 begin=7385 frame=7385 base={base} links=1201',
            'MIDZ_RESET_SCENE index=1 frame=7386 scene=501',
            'MIDZ_RESET_RESULT complete=1 requested=1 ready=1 scenes=1','MIDZ_RESET_GPU_RESULT complete=1 count=1']
        (root/'stdout.log').write_text('',encoding='utf-8');self.write(root,lines)
        return lines

    def write(self,root,lines):(root/'stderr.log').write_text('\n'.join(lines)+'\n',encoding='utf-8')

    def test_reset_requires_matching_gpu_boundary_fresh_proofs_and_actual_action(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);lines=self.fixture(root)
            self.assertTrue(r.verify({'mode':'continuous'},root,8000)['passed'])
            for n in range(len(lines)):
                for altered in (lines[:n]+lines[n+1:],lines+[lines[n]]):
                    self.write(root,altered)
                    with self.assertRaises(ValueError):r.verify({'mode':'continuous'},root,8000)
            for old,new in (('scene=500','scene=499'),('generation=1500','generation=1499'),
                            ('0123456789abcdef','0123456789abcdee'),('index=1','index=2')):
                changed=lines.copy();changed[1]=changed[1].replace(old,new);self.write(root,changed)
                with self.assertRaises(ValueError):r.verify({'mode':'continuous'},root,8000)
            self.write(root,lines)
            with self.assertRaises(ValueError):r.verify(None,root,8000)
            (root/'session-action-events.csv').write_text('id,event,frame,time\n1,request,6000,105\n',encoding='utf-8')
            with self.assertRaises(ValueError):r.verify({'mode':'continuous'},root,8000)

    def test_pristine_startup_then_active_reset_keeps_separate_proofs(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);active=self.fixture(root);base=112061
            pool=list(struct.unpack('<'+'I'*((root/'exotica-reset-1-bootstrap.bin').stat().st_size//4),
                (root/'exotica-reset-1-bootstrap.bin').read_bytes()))
            pool[2:4]=[1000,1000]
            (root/'exotica-bootstrap.bin').write_bytes(struct.pack('<'+'I'*len(pool),*pool))
            scene=list(struct.unpack('<16I',(root/'exotica-reset-1-scene.bin').read_bytes()))
            scene[2:4]=[1001,1000];scene[14]=1
            (root/'exotica-bootstrap-scene.bin').write_bytes(struct.pack('<16I',*scene))
            bootstrap=['MIDZ_BOOTSTRAP=3',f'MIDZ_BOOTSTRAP_READY begin=1000 frame=1000 base={base} links=1201',
                'MIDZ_BOOTSTRAP_SCENE frame=1001 scene=1','MIDZ_BOOTSTRAP_RESULT complete=1 frame=1000']
            startup='MIDZ_RESET_STARTUP index=1 frame=89 prepared=0 generation=0 epoch=0'
            lines=[startup,*bootstrap,*active,'MIDZ_RESET_STARTUP_RESULT count=1']
            (root/'session-actions.csv').write_text('frame,action\n90,soft_reset\n6000,soft_reset\n',encoding='utf-8')
            (root/'session-action-events.csv').write_text(
                'id,event,frame,time\n1,request,90,1\n1,complete,90,1\n2,request,6000,105\n2,complete,6000,105\n',encoding='utf-8')
            self.write(root,lines)
            result=r.verify({'mode':'continuous'},root,8000)
            self.assertEqual(result['startup']['resets'],[dict(index=1,frame=89)])
            self.assertEqual(len(result['resets']),1)
            self.assertEqual(result['actions']['completed'],2)
            entries=['MIDZ_RESET_ENTRY frame=89 fifo_empty=1','MIDZ_RESET_ENTRY frame=5999 fifo_empty=1']
            def with_entries(values):
                return [values[0],*lines[:5],*values[1:],*lines[5:]]
            self.write(root,with_entries(entries))
            self.assertEqual(r.verify({'mode':'continuous'},root,8000)['pre_device']['frames'],[89,5999])
            for bad in (entries[:1],entries[::-1],[entries[0],entries[1].replace('empty=1','empty=0')],entries+[entries[0]]):
                self.write(root,with_entries(bad))
                with self.assertRaises(ValueError):r.verify({'mode':'continuous'},root,8000)
            self.write(root,lines+entries)
            with self.assertRaises(ValueError):r.verify({'mode':'continuous'},root,8000)

            for bad in ('index=2','frame=90','frame=1000','prepared=1','generation=1','epoch=1'):
                old=bad.split('=')[0]+'='+dict(index='1',frame='89',prepared='0',generation='0',epoch='0')[bad.split('=')[0]]
                self.write(root,[line.replace(old,bad) if line==startup else line for line in lines])
                with self.assertRaises(ValueError):r.verify({'mode':'continuous'},root,8000)
            # With no active reset there must be no synthetic GPU reset/proof.
            self.write(root,[startup,*bootstrap,'MIDZ_RESET_STARTUP_RESULT count=1'])
            for p in root.glob('exotica-reset-*.bin'):p.unlink()
            (root/'session-actions.csv').write_text('frame,action\n90,soft_reset\n',encoding='utf-8')
            (root/'session-action-events.csv').write_text(
                'id,event,frame,time\n1,request,90,1\n1,complete,90,1\n',encoding='utf-8')
            result=r.verify({'mode':'continuous'},root,8000)
            self.assertEqual(result['resets'],[])
            self.assertTrue(result['startup']['bootstrap']['passed'])

    def test_corrupt_proof_phase_order_and_unscheduled_reset_reject(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);lines=self.fixture(root)
            self.write(root,[lines[2],*lines[:2],*lines[3:]])
            with self.assertRaises(ValueError):r.verify({'mode':'continuous'},root,8000)
            self.write(root,lines)
            for name in ('bootstrap','scene'):
                p=root/f'exotica-reset-1-{name}.bin';data=p.read_bytes()
                p.write_bytes(data[:-4]+bytes(4))
                # Pool sentinel was already zero: corrupt a link/signature instead.
                bad=bytearray(data);bad[20]^=1;p.write_bytes(bad)
                with self.assertRaises(ValueError):r.verify({'mode':'continuous'},root,8000)
                p.write_bytes(data)
            (root/'session-actions.csv').unlink()
            with self.assertRaises(ValueError):r.verify({'mode':'continuous'},root,8000)

if __name__=='__main__':unittest.main()
