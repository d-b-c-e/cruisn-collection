from pathlib import Path
import json, shutil, sys
sys.path.insert(0,'harness')
import graphics_options as G
from diagnostic_runtime import diagnostic_env, execute
from session_case import Recording, set_option
from game_patch import read_patch
from verification import write_json, sha256_file
import replay
root=Path.cwd()
out=root/'results/diagnostics/graphics-menu-20260907'
parent=root/'results/diagnostics/world-germany-extended-20260906'
manifest=json.loads((parent/'case.json').read_text())
section={'world_distance_crusnwld':'3','world_lookahead_crusnwld':'8','terrain_visibility_crusnwld':'1'}
rig=out/'seed'
shutil.copytree(parent/'initial',rig)
settings={k:v for k,v in manifest['settings'].items() if k!='MIDV_PATCH' and not k.startswith(('MIDV_WORLD_','MIDV_SCENERY'))}
settings.update(MIDV_GL='1',MIDV_GL_SCALE='4',MIDV_GL_CRT='1',MIDV_GL_MARGIN='86',MIDV_GL_LOG='1',MIDV_GL_SNAP='enabled',MIDV_GL_SNAP_FIRST='2300',MIDV_GL_SNAP_LAST='2400',MIDV_GL_SNAP_EVERY='50',MIDV_GL_SNAP_MAX='3')
settings.update(G.launch_overrides(root,rig,'crusnwld24',86,4,section,{}))
assert settings['MIDV_WORLD_FAR']=='240000' and settings['MIDV_WORLD_LEAD']=='8'
assert read_patch(settings['MIDV_PATCH'])[0x40]==(80000,240000)
command=['E:/Source/mame-src/vunit.exe',*manifest['command'][1:]]
command=set_option(command,'-resolution','1280x720')
command+=['-window','-nomaximize']
recording=Recording(str(out/'case'),every=60,stop_frame=2404)
command,env,runtime=recording.prepare(command,diagnostic_env(settings),rig,stimulus=parent/'record/input/session.inp')
result=execute(command,runtime,env,180)
shutil.copy2(runtime/'stdout.log',runtime/'launch.log')
recording.finish(result['returncode'])
assert recording.manifest['status']=='recorded',recording.manifest.get('error')
code=replay.main([str(recording.path),'--output',str(out/'replay'),'--compare-gl','--timeout','180'])
report={'passed':code==0,'scope':'launcher settings resolution, native activation, INP recording/replay and completed GL repeatability; short derived prefix, not original-route or attended acceptance','physical_force':False,'selection':section,'native_sha256':sha256_file(Path(command[0])),'source_commit':recording.manifest['collection_source'],'recording':str(recording.path),'replay_report':str(out/'replay/report.json'),'settings':recording.manifest['settings']}
write_json(out/'report.json',report)
assert code==0
print('MENU DISTANCE RECORD/REPLAY PASS',flush=True)
