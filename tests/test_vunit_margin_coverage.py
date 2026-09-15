"""Pixel coverage must preserve textured affine mapping and every center pixel."""
from pathlib import Path
import sys,unittest
import moderngl
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gpu'))
import renderer as r


class MarginCoverageTests(unittest.TestCase):
    def test_both_margins_preserve_original_texture_at_native_and_quality_scale(self):
        ctx=moderngl.create_standalone_context(require=430)
        try:
            program=ctx.program(vertex_shader=r.VS,fragment_shader=r.FS)
            texture=ctx.texture((4096,16),1,(np.arange(65536,dtype='uint32')%255+1).astype('u1').tobytes(),dtype='u1')
            texture.use(0)
            q=np.zeros((1,16),dtype='<u2')
            q[0,:10]=[0x100,256,65528,0,519,0,519,15,65528,15]
            q[0,10:14]=[0,254,0xfefe,0xfe00]
            f,u=r.build_vertices(q,8)
            for scale in [1,4]:
                with self.subTest(scale=scale):
                    for key,value in dict(uCanvas=(528.,16.),uScale=scale,uClipRight=527,
                        texram=0,texMask=65535,uDbgQuadId=0,uClipW=528,uBgMargin=0).items():program[key].value=value
                    idx=ctx.texture((528*scale,16*scale),1,dtype='u2');mask=ctx.texture((528*scale,16*scale),1,dtype='u1')
                    target=ctx.framebuffer([idx,mask]);target.use();ctx.viewport=(0,0,528*scale,16*scale)
                    images=[]
                    for tagged in [False,True]:
                        meta=u.copy()
                        if tagged:meta[:,2]|=16
                        vf,vu=ctx.buffer(f.tobytes()),ctx.buffer(meta.tobytes())
                        vao=ctx.vertex_array(program,[(vf,'2f 2f 2f 2f 2f 4f 4f 4f','in_corner','in_v0','in_v1','in_v2','in_v3','in_uv01','in_uv23','in_uvBounds'),(vu,'4u','in_meta')])
                        target.clear();vao.render(moderngl.TRIANGLES)
                        images.append(np.frombuffer(target.read(components=1,dtype='u2'),'<u2').reshape(16*scale,528*scale).copy())
                        vao.release();vf.release();vu.release()
                    original,clipped=images
                    self.assertTrue(np.any(original[:,8*scale:520*scale]))
                    self.assertFalse(np.any(clipped[:,8*scale:520*scale]))
                    for region in [slice(0,8*scale),slice(520*scale,None)]:
                        self.assertTrue(np.any(clipped[:,region]))
                        np.testing.assert_array_equal(clipped[:,region],original[:,region])
                    target.release();idx.release();mask.release()
            texture.release();program.release()
        finally:ctx.release()


if __name__=='__main__':unittest.main()
