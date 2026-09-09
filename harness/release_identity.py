"""Content identity for release evidence, including uncommitted product changes."""
import hashlib
from pathlib import Path
import subprocess

PREFIXES = ('harness/','gpu/','lua/','native/','lib/','profiles/','patch/','fixtures/','tests/','.github/','media/','third_party/')
FILES = {'build_local.ps1','make_release.ps1','setup.ps1','requirements-test.txt'}
TEXT = {'.py','.lua','.h','.cpp','.json','.ini','.txt','.patch','.ps1','.yml','.yaml','.md',
        '.csv','.cfg','.xml','.example'}
TEXT_NAMES = {'LICENSE','COPYING','VERSION'}


def canonical_bytes(path, data):
    # Git's Windows checkout can add CRLF to extensionless licences and profile
    # examples too. Do not let checkout style masquerade as a source change.
    # Binary fixtures (including extensionless NVRAM) always retain their bytes.
    if (path.suffix in TEXT or path.name in TEXT_NAMES) and b'\0' not in data:
        return data.replace(b'\r\n', b'\n')
    return data


def source_identity(root):
    root = Path(root)
    names = subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=root).decode().split('\0')
    hashes = {}
    for name in sorted(set(names)):
        if not name or not (name.startswith(PREFIXES) or name in FILES): continue
        path = root/name
        data = path.read_bytes()  # Deleted tracked inputs invalidate evidence too.
        data=canonical_bytes(path,data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    payload=''.join(f'{name}\0{digest}\n' for name,digest in hashes.items()).encode()
    return {'sha256':hashlib.sha256(payload).hexdigest(),'files':hashes}
