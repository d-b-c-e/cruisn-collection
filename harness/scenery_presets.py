"""Explicit candidate presets for the qualified continuous host renderer paths.

These compose existing guarded controls; they do not enable a shipped feature,
relax native validation or establish equal visible distance across games.
"""
NAME = 'continuous-3x'
VUNIT = '''--vunit-bootstrap scenes --vunit-host-failure original
--vunit-runtime continuous --vunit-journals quiet --gl-height 400'''.split()
DISPLAY = '--gl-crt on --gl-scale 4'.split()
WORLD = '''--world-host-scenery draw --world-host-source future
--world-host-layer both --world-host-first 1800 --world-host-last 2250
--world-host-log summary --world-host-far 240000 --world-host-roads on
--world-host-far-coverage on --world-host-active-roads margins'''.split()
PROFILES = {
    'crusnusa': '''--usa-host-scenery draw --usa-host-source future
--usa-host-first 3500 --usa-host-last 3600 --usa-host-far 240000
--usa-host-log summary'''.split()+VUNIT+DISPLAY,
    'crusnwld24': WORLD+VUNIT+DISPLAY,
    'crusnwld': WORLD+VUNIT+DISPLAY,
    'offroadc': '''--offroad-host-scenery draw --offroad-host-source future
--offroad-host-layer both --offroad-host-first 1800 --offroad-host-last 2250
--offroad-host-log summary --offroad-host-distance 3
--offroad-host-partial recover'''.split()+VUNIT+DISPLAY,
    'crusnexo': '''--gl-log --zeus-palette guard --zeus-margin-clear page
--zeus-sky repeat --exotica-host-scene observe --exotica-host-first 1800
--exotica-host-last 5240 --exotica-host-multiplier 3
--exotica-host-materials observe --exotica-host-material-pages written
--exotica-host-bounds on --exotica-host-source-cache on
--exotica-host-early-depth on --exotica-host-future draw
--exotica-host-future-present extended --zeus-depth-mirror wide
--zeus-depth-first 2 --zeus-depth-last 5241 --exotica-lifetimes observe
--exotica-lifetime-first 1799 --exotica-lifetime-last 5242
--exotica-host-waiting observe --exotica-host-fence observe
--exotica-host-handover draw --exotica-host-active draw
--exotica-host-compose margins --exotica-model-endpoint draw
--exotica-endpoint-scope marked --exotica-endpoint-first 1800
--exotica-endpoint-last 5240 --exotica-endpoint-snapshot 0
--exotica-endpoint-admit-from 1800 --exotica-early-visibility endpoint
--exotica-journals quiet --exotica-bootstrap scenes
--exotica-shutdown observe --exotica-runtime continuous'''.split()+DISPLAY,
}
MANAGED = frozenset(word for profile in PROFILES.values() for word in profile if word.startswith('--'))


def add_arguments(parser):
    parser.add_argument('--scenery-preset', choices=(NAME,),
        help='candidate-only continuous3x host scenery for the recorded ROM; owns CRT4x/native-height and renderer controls, physical FFB remains off')


def expand(argv, rom):
    if rom not in PROFILES:
        raise ValueError('no qualified continuous scenery profile for ROM '+str(rom))
    result=[];seen=0;i=0
    while i<len(argv):
        word=argv[i];key=word.split('=',1)[0]
        if key=='--scenery-preset':
            if '=' in word:
                value=word.split('=',1)[1]
            else:
                i+=1
                if i==len(argv):raise ValueError('missing scenery preset')
                value=argv[i]
            if value!=NAME:raise ValueError('unsupported scenery preset')
            seen+=1
        else:
            if key in MANAGED:
                raise ValueError('scenery preset owns '+key+'; use explicit controls for a variant')
            result.append(word)
        i+=1
    if seen!=1:raise ValueError('select exactly one scenery preset')
    controls=list(PROFILES[rom])
    return result+controls,dict(name=NAME,rom=rom,controls=controls,physical_force=False,
        scope='Existing continuous CLI candidate controls, including capture reference bounds that do not stop runtime. Not deployed, no equal-visible-distance or release acceptance claim.')
