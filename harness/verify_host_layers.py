"""ROM-free GPU checks for auxiliary scenery and foreground coverage ownership."""
import argparse
from pathlib import Path
import sys
import moderngl
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gpu'))
import renderer as R
from verification import write_json


def resolve(ctx,index,mask,*,layered=True,fill=4):
    h,w=index.shape
    prog=ctx.program(vertex_shader=R.PAL_VS,fragment_shader=R.PAL_FS)
    settings=dict(idxTex=0,palTex=1,maskTex=2,uCrop=0,uCrt=0,uSrcH=float(h),uFillR=fill,uMargin=0)
    if 'uHostLayers' in prog:settings['uHostLayers']=int(layered)
    for name,value in settings.items():prog[name].value=value
    palette=np.zeros((128,256),np.uint32);palette.ravel()[16]=0x7c00;palette.ravel()[37]=0x03e0
    inputs=[ctx.texture((w,h),1,index.tobytes(),dtype='u2'),ctx.texture((256,128),1,palette.tobytes(),dtype='u4'),ctx.texture((w,h),1,mask.tobytes(),dtype='u1')]
    for unit,texture in enumerate(inputs):texture.use(unit)
    color=ctx.texture((w,h),4,dtype='f1');target=ctx.framebuffer([color]);target.use();ctx.viewport=(0,0,w,h)
    vao=ctx.vertex_array(prog,[]);vao.render(moderngl.TRIANGLES,vertices=3)
    result=np.frombuffer(color.read(alignment=1),np.uint8).reshape(h,w,4).copy()
    for resource in [vao,target,color,*inputs,prog]:resource.release()
    return result


def checks(ctx):
    index=np.full((24,32),37,np.uint16);mask=np.full(index.shape,5,np.uint8)
    index[6:18,4:28]=16;mask[6:18,4:28]=1
    index[11,4:28]=37;mask[11,4:28]=5
    legacy=resolve(ctx,index,mask,layered=False);candidate=resolve(ctx,index,mask)
    outcomes=[dict(check='auxiliary-pixels-do-not-close-foreground-cracks',
        legacy_green_gap=int(np.count_nonzero(legacy[11,4:28,1])),
        candidate_green_gap=int(np.count_nonzero(candidate[11,4:28,1])),
        passed=bool(np.all(candidate[6:18,4:28,:3]==[255,0,0]) and np.any(legacy[11,4:28,1]))),
      dict(check='auxiliary-silhouette-is-preserved',passed=bool(np.array_equal(candidate[:5],legacy[:5]) and np.all(candidate[:5,:,:3]==[0,255,0])))]
    # The material's dither tag survives auxiliary ownership tagging. The
    # palette resolve must still average only explicitly tagged shadow pairs.
    yy,xx=np.indices(index.shape);odd=(xx^yy)&1
    index=np.where(odd,37,16).astype(np.uint16)
    base=np.where(odd,1,3).astype(np.uint8)
    expected=resolve(ctx,index,base,layered=False,fill=0)
    actual=resolve(ctx,index,base|4,fill=0)
    outcomes.append(dict(check='auxiliary-dither-material-tag',passed=bool(np.array_equal(expected,actual))))
    # No auxiliary geometry: enabling the extra layer path cannot alter normal
    # shadows or the existing nearest-neighbor crack repair.
    mask=np.ones(index.shape,np.uint8);mask[11,4:28]=0
    outcomes.append(dict(check='ordinary-coverage-unchanged',passed=bool(np.array_equal(resolve(ctx,index,mask,layered=False),resolve(ctx,index,mask)))))
    # Exercise the geometry shader's actual ownership output, including dither
    # and transparent texture holes. Metadata may never turn discarded texels
    # into written pixels or erase the hardware material tag.
    from verify_quality import render,rectangle
    texture=np.full(65536,37,np.uint8)
    for mode,scale,tag in ((0x100,4,5),(0x2100,4,7),(0x2100,1,5)):
        quads=rectangle(mode=mode)[None,:]
        ordinary,base_mask=render(ctx,quads,texture,scale)
        auxiliary,aux_mask=render(ctx,quads,texture,scale,meta_bits=8)
        outcomes.append(dict(check='shader-auxiliary-material-ownership',mode=mode,scale=scale,
            passed=bool(np.array_equal(ordinary,auxiliary) and np.any(aux_mask==tag)
                and np.array_equal(base_mask,aux_mask&3) and np.all(aux_mask[base_mask==0]==0))))
    transparent=rectangle(mode=0x900)[None,:]
    _,mask=render(ctx,transparent,np.zeros(65536,np.uint8),4,meta_bits=8)
    outcomes.append(dict(check='auxiliary-transparent-texels-stay-unwritten',passed=bool(not np.any(mask))))
    return outcomes


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    report=dict(passed=False,scope=__doc__)
    try:
        ctx=moderngl.create_context(standalone=True,require=430)
        report['renderer']=ctx.info['GL_RENDERER'];report['checks']=checks(ctx)
        report['passed']=all(r['passed'] for r in report['checks']);ctx.release()
    except Exception as error:report['error']=str(error)
    write_json(args.report,report);print('PASS' if report['passed'] else 'FAIL',report)
    return int(not report['passed'])


if __name__=='__main__':raise SystemExit(main())
