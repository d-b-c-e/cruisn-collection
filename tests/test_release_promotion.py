import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from promote_release import verify_identity


class PromotionTests(unittest.TestCase):
    def test_review_of_another_zip_cannot_publish_current_candidate(self):
        checked={'package_sha256':'zip','candidate_sha256':'exe','file_hashes':{'vunit.exe':'exe'},
                 'media':True,'version':'v0.4.0'}
        manifest=dict(checked,schema=1,source_clean=True,source_identity='source',commit='a'*40)
        ledger={'checks':{'shared/package-review':{'evidence':[{'sha256':'zip'}]}}}
        self.assertEqual(verify_identity(manifest,checked,ledger,'source'),'v0.4.0')
        for change in ({'source_identity':'old'},{'source_clean':False},{'package_sha256':'other'},
                       {'file_hashes':{}},{'version':'dev'},{'commit':'branch-name'}):
            with self.assertRaises(ValueError):
                verify_identity(dict(manifest,**change),checked,ledger,'source')
        bad=copy.deepcopy(ledger);bad['checks']['shared/package-review']['evidence'][0]['sha256']='other'
        with self.assertRaisesRegex(ValueError,'exact ZIP'):
            verify_identity(manifest,checked,bad,'source')
