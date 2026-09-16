from pathlib import Path
import json,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import binary_provenance as p
from verification import sha256_file

class ProvenanceTests(unittest.TestCase):
    def fixture(self,root):
        exe=root/'vunit.exe';exe.write_bytes(b'not launched')
        export=root/'export.json';data=dict(passed=True,candidate_sha256=sha256_file(exe),
            native_commit='a'*40,tree='b'*40,patch_sha256='c'*64,build_log_sha256='d'*64)
        export.write_text(json.dumps(data),encoding='utf-8');return exe,export,data

    def test_missing_receipt_is_unknown_and_valid_receipt_binds_exact_binary(self):
        with tempfile.TemporaryDirectory() as temp:
            exe,export,data=self.fixture(Path(temp))
            self.assertIsNone(p.read(exe))
            path=p.attach(exe,export);result=p.read(exe)
            self.assertEqual(result['commit'],data['native_commit'])
            self.assertEqual(result['receipt_sha256'],sha256_file(path))
            with self.assertRaises(ValueError):p.attach(exe,export)
            exe.write_bytes(b'changed executable')
            with self.assertRaises(ValueError):p.read(exe)

    def test_malformed_or_unmatched_attestation_cannot_be_attached(self):
        with tempfile.TemporaryDirectory() as temp:
            exe,export,data=self.fixture(Path(temp))
            for changes in ({'passed':False},{'candidate_sha256':'0'*64},{'native_commit':'main'},
                            {'tree':'b'*39},{'patch_sha256':None}):
                export.write_text(json.dumps(data|changes),encoding='utf-8')
                with self.subTest(changes=changes),self.assertRaises(ValueError):p.attach(exe,export)
                self.assertFalse(p.receipt_path(exe).exists())
            export.write_text(json.dumps(data),encoding='utf-8');path=p.attach(exe,export)
            valid=json.loads(path.read_text(encoding='utf-8'))
            for changed in (valid|{'schema':True},valid|{'personal_setting':80},valid|{'executable_sha256':'0'*64}):
                path.write_text(json.dumps(changed),encoding='utf-8')
                with self.assertRaises(ValueError):p.read(exe)

if __name__=='__main__':unittest.main()
