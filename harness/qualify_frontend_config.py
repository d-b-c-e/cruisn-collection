"""Frozen launcher configuration smoke; no window, device or emulator entry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--executable',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();exe=args.executable.resolve();out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    report={'scope':'Frozen configuration only; no GPU, device, game or force output',
            'executable':str(exe),'executable_sha256':sha(exe),'checks':[]}
    fixtures={
        'fresh':None,
        'legacy':'[collection]\nffb=0\nffb_spring=37\ncrt=0\n[wheelmap]\nsteer=Owner|axis:0:0:neg\n[telemetry]\nforza=192.0.2.5:9876\n',
        'saved-off':'[collection]\nffb=65\nffb_enabled=0\nsettings_view=advanced\nsettings_page=ffb\nffb_profile=owner@7\n[telemetry]\nenabled=0\nforza=192.0.2.5:9876\n',
    }
    for name,config in fixtures.items():
        root=out/name;root.mkdir();cfg=root/'rig/collection.ini'
        if config is not None:
            cfg.parent.mkdir();cfg.write_text(config,encoding='utf-8')
        before=cfg.read_bytes() if cfg.exists() else None
        result=root/'config-report.json'
        env=dict(os.environ,CRUISN_HOME=str(root),MIDV_FFB='0')
        run=subprocess.run([str(exe),'--config-report',str(result)],env=env,timeout=30)
        assert run.returncode==0,(name,run.returncode)
        data=json.loads(result.read_text(encoding='utf-8'));state=data['settings']
        after=cfg.read_bytes() if cfg.exists() else None
        assert before==after,(name,'configuration mutated')
        if name=='fresh':
            assert state['settings_view']=='simple' and state['settings_page']=='setup'
            assert state['crt'] and state['scale']==4 and state['ffb_enabled']
        elif name=='legacy':
            assert not state['ffb_enabled'] and state['ffb']==0 and state['ffbspring']==37 and not state['crt']
            assert state['bindings']['steer']=='Owner|axis:0:0:neg'
            assert state['telemetry']['forza']=='192.0.2.5:9876'
        else:
            assert not state['ffb_enabled'] and state['ffb']==65 and state['ffbprofile']=='owner@7'
            assert state['settings_view']=='advanced' and state['settings_page']=='ffb'
            assert state['telemetry']['enabled']=='0' and state['telemetry']['forza']=='192.0.2.5:9876'
        report['checks'].append(dict(case=name,passed=True,report_sha256=sha(result)))
    report['passed']=True
    (out/'qualified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
