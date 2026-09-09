"""Revision-specific imported MAME cheats; expressions are executed only by MAME."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import zipfile
from xml.etree import ElementTree as ET

ROMS = ('crusnusa', 'crusnwld24', 'crusnwld', 'offroadc', 'crusnexo')
MAX_XML = 256 * 1024


def read_7z_member(tar, archive, name):
    """Bound decompressed bytes as well as archive size and extraction time."""
    with subprocess.Popen([tar,'-xOf',str(archive),name],stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL) as process:
        output = []
        reader = threading.Thread(target=lambda: output.append(process.stdout.read(MAX_XML+1)),daemon=True)
        reader.start()
        try:
            reader.join(30)
            if reader.is_alive(): raise ValueError('Cheat archive extraction timed out')
            if output and len(output[0]) > MAX_XML: raise ValueError('Oversized cheat XML')
            return output[0] if process.wait(timeout=2) == 0 else None
        finally:
            if process.poll() is None: process.kill()
            process.wait(); reader.join(2)


def metadata(data):
    if len(data) > MAX_XML or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('Cheat XML is too large or contains unsupported declarations')
    root = ET.fromstring(data)
    if root.tag != 'mamecheat' or root.get('version') != '1':
        raise ValueError('Expected MAME cheat XML version 1')
    entries = []
    for index, entry in enumerate(root.findall('cheat'), 1):
        description = entry.get('desc') or ''
        if not description.strip() or len(description) > 200 or index > 128:
            raise ValueError('Invalid or oversized cheat catalog')
        scripts = {s.get('state'): s for s in entry.findall('script')}
        parameter = entry.find('parameter')
        choices = ['OFF']
        reason = ''
        if parameter is not None:
            items = parameter.findall('item')
            if items:
                choices += [(i.text or '').strip() for i in items]
            else:
                def number(name, default):
                    value = parameter.get(name, str(default))
                    if value.startswith('$'): return int(value[1:], 16)
                    if value.lower().startswith('0x'): return int(value, 16)
                    return int(value.lstrip('#'), 10)
                low, high, step = number('min', 0), number('max', 0), number('step', 1)
                if step <= 0 or low < 0 or high < low or (high-low)//step > 63:
                    raise ValueError('Cheat parameter range is unsupported')
                choices += [str(v) for v in range(low, high+1, step)]
                # MAME clamps the final step to max even when the range does
                # not divide evenly. Keep menu indices identical to its engine.
                if choices[-1] != str(high): choices.append(str(high))
            if 'run' not in scripts and 'off' not in scripts and 'change' in scripts:
                reason = 'Use Esc > Cheats during gameplay to activate this action.'
        elif 'run' in scripts or ('on' in scripts and 'off' in scripts):
            choices.append('ON')
        else:
            reason = 'One-shot or information entry; use Esc > Cheats during gameplay.'
        # Saving/restoring instruction words at boot can capture uninitialised
        # code. Keep these in the live menu, never in pre-race preferences.
        if 'off' in scripts:
            reason = 'Use Esc > Cheats after the game has loaded; this action restores game code.'
        if len(choices) > 65 or any(not c or len(c) > 100 for c in choices):
            raise ValueError('Invalid cheat choices')
        entries.append({'index':index, 'description':description, 'choices':choices,
                        'comment':entry.findtext('comment', '').strip(), 'unavailable':reason})
    return entries


def import_files(source, rig):
    """Import exact root-level arcade names; never console entries or parent fallback."""
    source, rig = Path(source), Path(rig)
    found = {}
    if source.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('Cheat archive exceeds 64 MB')
    with tempfile.TemporaryDirectory(prefix='cruisn-cheat-import-') as tmp:
        archive = source
        if source.suffix.lower() == '.xml':
            if source.stem not in ROMS:
                raise ValueError('XML filename must match a supported arcade ROM revision')
            found[source.stem] = source.read_bytes()
        elif source.suffix.lower() == '.zip':
            with zipfile.ZipFile(source) as z:
                for rom in ROMS:
                    name = rom+'.xml'
                    if name in z.namelist():
                        if z.getinfo(name).file_size > MAX_XML: raise ValueError('Oversized cheat XML')
                        found[rom] = z.read(name)
                if not found and 'cheat.7z' in z.namelist():
                    if z.getinfo('cheat.7z').file_size > 64*1024*1024: raise ValueError('Oversized nested archive')
                    archive = Path(tmp)/'cheat.7z'; archive.write_bytes(z.read('cheat.7z'))
        elif source.suffix.lower() != '.7z':
            raise ValueError('Choose a MAME cheat XML, ZIP or 7z archive')
        if archive.suffix.lower() == '.7z':
            tar = shutil.which('tar')
            if not tar: raise ValueError('Importing 7z needs Windows tar; alternatively import extracted XML files')
            for rom in ROMS:
                data = read_7z_member(tar,archive,rom+'.xml')
                if data is not None: found[rom] = data
        if not found: raise ValueError('No supported arcade cheat entries found in this file')
        catalogs = {rom: metadata(data) for rom,data in found.items()}  # validate whole import first
        target = rig/'cheats'; target.mkdir(parents=True,exist_ok=True)
        for rom,data in found.items():
            path = target/(rom+'.xml')
            if path.exists() and path.read_bytes() != data:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                backup = target/'history'/digest; backup.mkdir(parents=True,exist_ok=True)
                shutil.copy2(path,backup/path.name)
            path.write_bytes(data)
        return {rom:len(rows) for rom,rows in catalogs.items()}


def catalog(rig, rom):
    if rom not in ROMS: return {'rom':rom,'sha256':None,'entries':[]}
    path = Path(rig)/'cheats'/(rom+'.xml')
    if not path.exists(): return {'rom':rom,'sha256':None,'entries':[]}
    data = path.read_bytes()
    return {'rom':rom,'sha256':hashlib.sha256(data).hexdigest(),'entries':metadata(data)}


def selections(rig, cat):
    path = Path(rig)/'cheats/settings.json'
    saved = json.loads(path.read_text()) if path.exists() else {}
    row = saved.get(cat['rom'], {})
    if row.get('sha256') != cat['sha256']: return {}
    choices = row.get('choices',{})
    return {str(e['index']): choices[str(e['index'])] for e in cat['entries']
            if not e['unavailable'] and type(choices.get(str(e['index']))) is int
            and 0 < choices[str(e['index'])] < len(e['choices'])}


def save(rig, cat, choices):
    path = Path(rig)/'cheats/settings.json'; path.parent.mkdir(parents=True,exist_ok=True)
    saved = json.loads(path.read_text()) if path.exists() else {}
    saved[cat['rom']] = {'sha256':cat['sha256'],'choices':choices}
    temp = path.with_suffix('.tmp'); temp.write_text(json.dumps(saved,indent=2),encoding='utf-8'); temp.replace(path)


def lua_string(value):
    return '"'+''.join('\\%03d'%b for b in value.encode('utf-8'))+'"'


def read_actions(path, selection, frames):
    """Validate a recorded action journal independently of the Lua consumer."""
    entries = {e['index']: e for e in selection['entries']}
    result = []
    previous = 1
    with Path(path).open(encoding='utf-8', newline='') as stream:
        reader = csv.reader(stream)
        if next(reader, None) != ['frame','index','steps','activate']:
            raise ValueError('invalid cheat action header')
        for row in reader:
            if len(row) != 4 or any(not v.isascii() or not v.isdigit() for v in row):
                raise ValueError('invalid cheat action row')
            frame, index, steps, activate = map(int, row)
            if (not previous <= frame <= frames or len(result) >= 100000 or
                    index not in entries or not 0 <= steps < len(entries[index]['choices']) or activate not in (0,1)):
                raise ValueError('invalid cheat action frame or selection')
            previous = frame
            result.append(dict(frame=frame,index=index,steps=steps,activate=activate))
    return result


def prepare(root, rig, rom):
    cat = catalog(rig,rom); selected = selections(rig,cat)
    if not cat["entries"]: return None
    bundle = Path(rig)/'cheats/runtime'/rom; bundle.mkdir(parents=True,exist_ok=True)
    shutil.copy2(Path(rig)/'cheats'/(rom+'.xml'),bundle/(rom+'.xml'))
    script = Path(root)/'lua/cheats.lua'
    if not script.exists(): script = Path(root)/'source/lua/cheats.lua'
    shutil.copy2(script,bundle/'cheats.lua')
    rows = []
    for entry in cat['entries']:
        count = selected.get(str(entry['index']),0)
        if count: rows.append('{index=%d,description=%s,steps=%d}'%(entry['index'],lua_string(entry['description']),count))
    menu = []
    for entry in cat['entries']:
        menu.append('{index=%d,description=%s,comment=%s,choices={%s}}' % (
            entry['index'], lua_string(entry['description']), lua_string(entry['comment']),
            ','.join(lua_string(choice) for choice in entry['choices'])))
    (bundle/'settings.lua').write_text('return {live_protocol=1,rom='+lua_string(rom)+
        ',entries={'+','.join(rows)+'},catalog={'+','.join(menu)+'}}\n',encoding='utf-8')
    (bundle/'selection.json').write_text(json.dumps(dict(cat,selected=selected,live_protocol=1),indent=2),encoding='utf-8')
    return bundle


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path);ap.add_argument('--rig',type=Path,default=Path(__file__).resolve().parents[1]/'rig')
    args = ap.parse_args()
    print(json.dumps(import_files(args.source,args.rig),indent=2))
