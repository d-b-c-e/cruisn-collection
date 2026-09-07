"""Content identity for release evidence, including uncommitted product changes."""
import hashlib
from pathlib import Path
import subprocess

PREFIXES = ('harness/','gpu/','lua/','native/','lib/','profiles/','patch/','fixtures/','tests/','.github/','media/','third_party/')
FILES = {'make_release.ps1','setup.ps1','requirements-test.txt'}
TEXT = {'.py','.lua','.h','.cpp','.json','.ini','.txt','.patch','.ps1','.yml','.yaml','.md'}


def source_identity(root):
    root = Path(root)
    names = subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=root).decode().split('\0')
    hashes = {}
    for name in sorted(set(names)):
        if not name or not (name.startswith(PREFIXES) or name in FILES): continue
        path = root/name
        data = path.read_bytes()  # Deleted tracked inputs invalidate evidence too.
        if path.suffix in TEXT: data=data.replace(b'\r\n',b'\n')
        hashes[name]=hashlib.sha256(data).hexdigest()
    payload=''.join(f'{name}\0{digest}\n' for name,digest in hashes.items()).encode()
    return {'sha256':hashlib.sha256(payload).hexdigest(),'files':hashes}
