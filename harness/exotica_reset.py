"""Verify scheduled quiescent Exotica reset, GPU boundary and fresh guest proofs."""
from pathlib import Path
import re
from exotica_bootstrap import verify_pool_proof,verify_scene_proof,verify as verify_bootstrap
from session_actions import verify as verify_actions,read_schedule,PLAN
from verification import sha256_file

def verify(trial,directory,frames):
    root=Path(directory);lines=[]
    for name in ('stdout.log','stderr.log'):
        path=root/name
        if not path.is_file() or path.stat().st_size>16*1024*1024:raise ValueError('reset receipt stream extent')
        lines.extend(x for x in path.read_text(encoding='utf-8',errors='replace').splitlines() if x.startswith('MIDZ_RESET'))
    proofs=sorted(root.glob('exotica-reset-*.bin'))
    scheduled=(root/PLAN).exists()
    if not trial or not scheduled:
        if lines or proofs:raise ValueError('unrequested extended renderer reset')
        return None
    actions=read_schedule(root/PLAN,frames);completed=verify_actions(root,frames)
    if not completed or completed['completed']!=len(actions):raise ValueError('missing scheduled reset completion')
    # A reset before any pool/scene transaction retains the original startup
    # proof. It must not masquerade as an active scene/GPU reseed.
    startups=[m for line in lines if (m:=re.fullmatch(
        r'MIDZ_RESET_STARTUP index=(\d+) frame=(\d+) prepared=0 generation=0 epoch=0',line))]
    startup_result=None;startup_frames=set()
    if startups:
        proof=verify_bootstrap(dict(mode='scenes',frames=frames,continuous=True),root)
        previous=0;rows=[]
        action_frames={a['frame']-1 for a in actions}
        for index,m in enumerate(startups,1):
            frame=int(m[2])
            if int(m[1])!=index or not previous<frame<proof['begin'] or frame not in action_frames:
                raise ValueError('startup reset order/action/readiness')
            startup_frames.add(frame);previous=frame
            rows.append(dict(index=index,frame=frame))
        final=f'MIDZ_RESET_STARTUP_RESULT count={len(startups)}'
        if lines.count(final)!=1:raise ValueError('startup reset completion')
        remove={m[0] for m in startups}|{final}
        lines=[line for line in lines if line not in remove]
        startup_result=dict(passed=True,resets=rows,bootstrap=proof,
            scope='Pristine pre-pool resets; no auxiliary geometry/materials or source epoch existed.')
    actions=[a for a in actions if a['frame']-1 not in startup_frames]
    patterns={
        'queued':r'MIDZ_RESET_QUEUED index=(\d+) frame=(\d+) scene=(\d+) generation=(\d+) hash=([0-9a-f]{16}) epoch=(\d+)',
        'gpu':r'MIDZ_RESET_GPU index=(\d+) frame=(\d+) scene=(\d+) generation=(\d+) hash=([0-9a-f]{16})',
        'ready':r'MIDZ_RESET_READY index=(\d+) begin=(\d+) frame=(\d+) base=(\d+) links=1201',
        'scene':r'MIDZ_RESET_SCENE index=(\d+) frame=(\d+) scene=(\d+)',
    }
    found={};recognized=[]
    for kind,pattern in patterns.items():
        matches=[m for line in lines if (m:=re.fullmatch(pattern,line))]
        if len(matches)!=len(actions):raise ValueError('missing or duplicate reset '+kind)
        found[kind]=matches;recognized.extend(m[0] for m in matches)
    count=len(actions)
    finals=[f'MIDZ_RESET_RESULT complete=1 requested={count} ready={count} scenes={count}',
            f'MIDZ_RESET_GPU_RESULT complete=1 count={count}'] if count else []
    if sorted(lines)!=sorted(recognized+finals):raise ValueError('extra or incomplete reset receipts')
    result=[];expected_proofs=[];last_scene=last_generation=last_epoch=0
    last_frame=startup_result['bootstrap']['scene_frame'] if startup_result else 0
    for offset,action in enumerate(actions):
        q,g,b,s=(found[k][offset] for k in ('queued','gpu','ready','scene'));index=offset+1
        if any(int(m[1])!=index for m in (q,g,b,s)):raise ValueError('reset index order')
        if q.groups()[:5]!=g.groups():raise ValueError('reset CPU/GPU material boundary differs')
        frame,scene,generation,epoch=int(q[2]),int(q[3]),int(q[4]),int(q[6])
        begin,ready,base=map(int,b.groups()[1:]);sf,serial=map(int,s.groups()[1:])
        if (frame!=action['frame']-1 or not last_frame<frame<begin<=ready<=sf<frames or
                scene<last_scene or generation<last_generation or epoch<=last_epoch or
                not scene<serial<2**64 or not 0<generation<2**64 or not epoch<2**64):
            raise ValueError('reset clock, epoch or scene progress')
        # CPU request, verified pool and first scene must occur in that order;
        # the asynchronous GPU receipt can interleave without changing ownership.
        if not lines.index(q[0])<lines.index(b[0])<lines.index(s[0]):raise ValueError('reset CPU phase order')
        pool=root/f'exotica-reset-{index}-bootstrap.bin';first=root/f'exotica-reset-{index}-scene.bin'
        verify_pool_proof(pool,begin,ready,base);verify_scene_proof(first,sf,ready,serial)
        expected_proofs.extend((pool,first))
        result.append(dict(index=index,frame=frame,scene_before=scene,scene_after=serial,epoch=epoch,
            generation=generation,material_hash=q[5],ready_frame=ready,scene_frame=sf,
            pool_sha256=sha256_file(pool),scene_sha256=sha256_file(first)))
        last_frame=sf;last_scene=serial;last_generation=generation;last_epoch=epoch
    if sorted(proofs)!=sorted(expected_proofs):raise ValueError('extra reset proof files')
    report=dict(passed=True,resets=result,actions=completed,scope='Scheduled pristine-startup or quiescent active resets only; interrupted-work resets and physical FFB remain unqualified.')
    if startup_result:report['startup']=startup_result
    return report
