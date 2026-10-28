import os
import unittest
from unittest.mock import patch

from tools.check_dependency_network import audit, parse_counts, trace, connection_summary


class DependencyNetworkTests(unittest.TestCase):
    def test_connection_metadata_distinguishes_local_and_external_without_preserving_addresses(self):
        summary=connection_summary('12 connect(3, {sa_family=AF_UNIX, sun_path="/fixture/socket"}, 16) = -1\n'
            '12 connect(3, {sa_family=AF_INET, sin_port=htons(443), sin_addr=inet_addr("192.0.2.10")}, 16) = -1\n'
            '12 connect(3, {sa_family=AF_INET, sin_port=htons(9), sin_addr=inet_addr("127.0.0.1")}, 16) = -1\n')
        self.assertEqual(summary['external_ports'],{'443':1})
        self.assertEqual(summary['unix'],1)
        self.assertEqual(summary['loopback'],1)
        self.assertNotIn('192.0.2.10',str(summary))
        self.assertNotIn('/fixture/socket',str(summary))
    def test_summary_counts_successful_and_failed_calls_without_payload(self):
        summary = ('% time seconds usecs/call calls errors syscall\n'
                   '------ ----------- ----------- --------- --------- ----------------\n'
                   ' 60.00 0.000006 6 1 1 connect\n'
                   ' 40.00 0.000004 4 1 socket\n'
                   '100.00 0.000010 5 2 1 total\n')
        self.assertEqual(parse_counts(summary), {'connect': 1, 'socket': 1})
        self.assertEqual(parse_counts(''), {})

    def test_unknown_or_raw_trace_output_cannot_be_treated_as_zero_activity(self):
        for text in ('strace: ptrace denied', 'connect(3, address, 16) = -1',
                     '0 0 0 1 socket\n0 0 0 1 socket'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_counts(text)

    def test_refuses_to_trace_the_owners_computer(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(RuntimeError, 'clean Linux'):
            audit()

    def test_child_environment_excludes_credentials_and_proxy_configuration(self):
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, {'GH_TOKEN': 'fixture', 'HTTPS_PROXY': 'fixture',
                                        'LD_LIBRARY_PATH': 'fixture'}), \
                patch('tools.check_dependency_network.subprocess.run') as run:
            folder = Path(directory)
            (folder / 'canary.counts').write_text('0 0 0 1 socket\n0 0 0 1 connect\n')
            run.return_value.returncode = 0
            self.assertEqual(trace('canary', folder, '/usr/bin/strace')['connect'], 1)
            command = run.call_args.args[0]
            self.assertIn('-c', command)
            self.assertIn('-f', command)
            environment = run.call_args.kwargs['env']
            self.assertNotIn('GH_TOKEN', environment)
            self.assertNotIn('HTTPS_PROXY', environment)
            self.assertNotIn('fixture', environment['LD_LIBRARY_PATH'])
