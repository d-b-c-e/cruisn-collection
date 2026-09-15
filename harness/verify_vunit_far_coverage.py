"""ROM-free far coverage shader checks: preserve UVs, transparency and foreground."""
import argparse
from pathlib import Path
import moderngl
import numpy as np
from verify_quality import rectangle,render
from verification import write_json

def checks(ctx):
    atlas=(np.arange(65536,dtype=np.uint32)%239).astype('u1')
    background=rectangle(0,0,19,11,0);background[1]=17
    foreground=rectangle(6,0,11,11,0);foreground[1]=99
    outcomes=[]
    for scale in (1,4):
        for mode in (0x100,0x900):
            middle=rectangle(2,2,14,10,mode)
            scene=np.array([background,middle,foreground])
            normal=render(ctx,scene,atlas,scale)
            under=render(ctx,np.array([background,foreground]),atlas,scale)
            masks=np.zeros((3,16),dtype='<f4')
            unchanged=render(ctx,scene,atlas,scale,far_masks=masks)
            masks[1,0]=-1
            rejected=render(ctx,scene,atlas,scale,far_masks=masks)
            masks[1]=[4,0,0,0,0,0,9,0,9,12,0,12,0,0,0,0]
            clipped=render(ctx,scene,atlas,scale,far_masks=masks)
            x=(np.arange(20*scale)+0.5)/scale
            expected=[np.where(x[None,:]<9,a,b) for a,b in zip(normal,under)]
            exact=lambda a,b:all(np.array_equal(x,y) for x,y in zip(a,b))
            outcomes.append(dict(scale=scale,mode=mode,unchanged_exact=exact(normal,unchanged),
                rejected_exact=exact(under,rejected),clipped_exact=exact(expected,clipped),
                changed_pixels=int(np.count_nonzero(normal[0]!=clipped[0])),
                passed=exact(normal,unchanged) and exact(under,rejected) and exact(expected,clipped)
                    and bool(np.any(normal[0]!=clipped[0]))))
    return outcomes

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    result=dict(passed=False,scope=__doc__)
    try:
        ctx=moderngl.create_context(standalone=True,require=430)
        result['renderer']=ctx.info['GL_RENDERER'];result['checks']=checks(ctx)
        result['passed']=all(v['passed'] for v in result['checks']);ctx.release()
    except Exception as exc:result['error']=str(exc)
    write_json(args.report,result);print('PASS' if result['passed'] else 'FAIL',args.report)
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
