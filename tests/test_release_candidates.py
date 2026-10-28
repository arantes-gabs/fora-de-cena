import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.release_candidates import REPOSITORY, gh, matrix, passed_report, require_context
from tools.ci_native import intel_compatibility


class DraftCandidateTests(unittest.TestCase):
    def context(self):
        return {'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':REPOSITORY,
                'GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_REF':'refs/heads/main',
                'GITHUB_ACTOR':'arantes-gabs','FDC_OWNER_CONFIRMED':'true',
                'FDC_EXPECTED_COMMIT':'a'*40,'GITHUB_SHA':'a'*40}

    def test_only_exact_owner_repository_main_reviewed_commit_can_request_a_draft(self):
        valid=self.context()
        self.assertEqual(require_context(valid),'a'*40)
        for key,value in [('GITHUB_REPOSITORY','fixture/other'),('GITHUB_REF','refs/heads/testing/mac-linux'),
                          ('GITHUB_ACTOR','fixture'),('GITHUB_TRIGGERING_ACTOR','fixture'),
                          ('FDC_OWNER_CONFIRMED','false'),('GITHUB_EVENT_NAME','pull_request'),
                          ('GITHUB_SHA','b'*40),('FDC_EXPECTED_COMMIT','main')]:
            with self.subTest(key=key),self.assertRaises(RuntimeError):
                require_context({**valid,key:value})

    def test_invalid_context_never_calls_github_or_uses_the_token(self):
        with patch.dict(os.environ,{'GH_TOKEN':'fixture'},clear=True), \
                patch('tools.release_candidates.subprocess.run') as run, \
                self.assertRaises(RuntimeError):
            gh(['api','repos/'+REPOSITORY+'/releases'])
        run.assert_not_called()

    def test_target_plan_is_fixed_and_cannot_accept_a_repository_or_shell_command(self):
        self.assertEqual(len(matrix('all')['include']),5)
        self.assertEqual({x['target'] for x in matrix('mac-linux')['include']},
                         {'macos-arm64','linux-x86_64','linux-arm64'})
        self.assertEqual(matrix('macos-arm64')['include'][0]['runner'],'macos-15')
        for value in ('../other','fixture/other','all; fixture'):
            with self.assertRaises(ValueError):
                matrix(value)

    def test_a_failed_or_different_version_report_cannot_be_uploaded_as_a_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            report=Path(directory)/'report.json'
            report.write_text(json.dumps({'ok':True,'frozen':False,'camera_opened':False}))
            with self.assertRaises(ValueError):
                passed_report(report)

    def test_intel_source_exception_does_not_hide_other_missing_or_unpinned_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'work').mkdir()
            report=root/'work/wheels.json'
            for errors in (['numpy: no compatible non-yanked wheel'],['mediapipe: dependency not pinned: fixture'],None):
                report.write_text(json.dumps({'target':'macos-x86_64','errors':errors}))
                with patch('tools.ci_native.ROOT',root),self.assertRaises(ValueError):
                    intel_compatibility()
            report.write_text(json.dumps({'target':'macos-x86_64','errors':['mediapipe: no compatible non-yanked wheel']}))
            with patch('tools.ci_native.ROOT',root):
                intel_compatibility()
