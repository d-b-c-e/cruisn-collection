from pathlib import Path
import json,hashlib
root=Path(__file__).parent;read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
manifest=read('manifest.json')
for name,digest in manifest['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
prs=read('all-prs.json');summary=read('summary.json')
assert len(prs)==len({p['number'] for p in prs})==summary['open_prs']==291
assert summary['head']=='7a8b22c8da43512787c0d841ca5439c16deb3224'
def relevant(path):return 'zeus' in path.lower() or path.startswith('src/devices/cpu/tms320c3x/') or path=='src/devices/video/poly.h'
selected={p['number']:p['headRefOid'] for p in prs if any(map(relevant,p['files']))}
assert selected=={6515:'24f7615cd676a4511582afc0177da3160a7c662d',13138:'ac80ac9d18f714a2eb2de7ba72389eeaf6cc2b41',
    16021:'67e1d2311f150e6b496001ab5366d6a603b5daca',16094:'54b7ec0720e1d3a3d26a2e881b06628f78732837'}
complete=read('large-pr-git.json');truncated=read('large-pr-truncated-api.json')
assert complete['receipt']['passed'] and read('large-pr-recheck.json')['passed']
assert len(complete['files'])==len(set(complete['files']))==3306
assert not truncated['receipt']['passed'] and len(truncated['files'])==3000 and truncated['receipt']['expected']==3301
assert set(truncated['files'])<set(complete['files'])
assert len(set(complete['files'])-set(truncated['files']))==306
assert next(p for p in prs if p['number']==13054)['files']==complete['files']
assert not any(map(relevant,complete['additional']))
changes=read('main-changes.json');assert len(changes['commits'])==3 and not any(map(relevant,changes['files']))
print('PASS291 PR inventories, complete3306-path Git comparison and unchanged4 relevant heads. Earlier API truncation retained.')
