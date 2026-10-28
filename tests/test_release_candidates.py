import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.release_candidates import REPOSITORY, __version__, draft, gh, main, matrix, passed_report, require_context, upload_asset
from tools.ci_native import intel_compatibility


class DraftCandidateTests(unittest.TestCase):
    def test_prepare_reuses_creation_response_and_exports_id_for_native_jobs(self):
        record={'id':123}
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'output'
            with patch('sys.argv',['release_candidates.py','prepare']), \
                    patch.dict(os.environ,{'GITHUB_OUTPUT':str(output)},clear=True), \
                    patch('tools.release_candidates.require_context'), \
                    patch('tools.release_candidates.draft',return_value=record) as lookup, \
                    patch('tools.release_candidates.source_zip',return_value=Path('fixture.zip')), \
                    patch('tools.release_candidates.upload') as send:
                main()
            lookup.assert_called_once_with(create=True)
            self.assertEqual(send.call_args.args[2],record)
            self.assertEqual(output.read_text(encoding='utf-8'),'release_id=123\n')

    def test_native_upload_fetches_exact_prepared_draft_id(self):
        record={'id':123,'tag_name':'v'+__version__,'draft':True,'prerelease':True,'target_commitish':'a'*40}
        with patch('tools.release_candidates.require_context',return_value='a'*40), \
                patch.dict(os.environ,{'FDC_DRAFT_RELEASE_ID':'123'},clear=True), \
                patch('tools.release_candidates.gh',return_value=json.dumps(record)) as call:
            self.assertEqual(draft()['id'],123)
        self.assertTrue(call.call_args.args[0][-1].endswith('/releases/123'))

    def test_prepared_draft_id_cannot_redirect_the_request(self):
        with patch('tools.release_candidates.require_context',return_value='a'*40), \
                patch.dict(os.environ,{'FDC_DRAFT_RELEASE_ID':'../other'},clear=True), \
                patch('tools.release_candidates.gh') as call, self.assertRaises(ValueError):
            draft()
        call.assert_not_called()

    def test_draft_lookup_uses_authenticated_list_and_does_not_create_a_duplicate(self):
        record={'id':123,'tag_name':'v'+__version__,'draft':True,'prerelease':True,'target_commitish':'a'*40}
        with patch('tools.release_candidates.require_context',return_value='a'*40), \
                patch('tools.release_candidates.gh',return_value=json.dumps([record])) as call:
            self.assertEqual(draft()['id'],123)
        self.assertEqual(call.call_count,1)
        self.assertIn('/releases?per_page=100',call.call_args.args[0][-1])

    def test_upload_is_scoped_to_fixed_repository_and_does_not_follow_redirects(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.zip';path.write_bytes(b'fixture')
            with patch('tools.release_candidates.require_context'), \
                    patch.dict(os.environ,{'GH_TOKEN':'fixture'},clear=True), \
                    patch('tools.release_candidates.http.client.HTTPSConnection') as factory:
                response=factory.return_value.getresponse.return_value
                response.status=307
                response.read.return_value=b'fixture'
                with self.assertRaisesRegex(RuntimeError,'HTTP 307'):
                    upload_asset(123,path)
                factory.assert_called_once_with('uploads.github.com',timeout=600)
                request=factory.return_value.request.call_args
                self.assertTrue(request.args[1].startswith('/repos/'+REPOSITORY+'/releases/123/assets?'))
                factory.return_value.close.assert_called_once()

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
