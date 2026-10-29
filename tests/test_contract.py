"""Offline checks: no model calls, account access or network operations."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = tomllib.loads((ROOT / 'extension.toml').read_text())
CLIENT = MANIFEST['client']


class Contract(unittest.TestCase):
    def test_install_requires_native_v2_runtime(self):
        self.assertEqual(MANIFEST['extension']['id'], 'opencode')
        self.assertEqual(CLIENT['protocol'], 'opencode-stream')
        self.assertEqual(CLIENT['binaries'], ['opencode'])
        self.assertEqual(CLIENT['install'], {'from': 'native'})
        self.assertNotIn('npm', CLIENT)

    def test_exact_session_and_prompt_boundary(self):
        run = CLIENT['run']
        self.assertEqual(run['prompt'], 'arg')
        for name in ('new_session', 'resume'):
            self.assertEqual(run[name], ['--session', '{value}'])
        self.assertEqual(run['args'][:4], ['run', '--standalone', '--format', 'json'])
        self.assertEqual(run['args'][-2:], ['--', '{prompt}'])
        self.assertEqual(run['args'].count('{session}'), 1)
        self.assertEqual(run['model'], ['-m', '{value}'])
        self.assertFalse({'--continue', '--server', '--fork'} & set(run['args']))

    def test_private_config_without_hardcoding_machine_data(self):
        self.assertEqual(CLIENT['home_env'], 'HOME')
        env = CLIENT['run']['env']
        for name in ('XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME',
                     'OPENCODE_CONFIG_DIR', 'OPENCODE_CONFIG', 'OPENCODE_TEST_HOME'):
            self.assertTrue(env[name].startswith('{home}'), name)
        self.assertNotIn('XDG_DATA_HOME', env)  # resolved by node before HOME replacement
        self.assertNotIn('OPENCODE_DB', env)
        self.assertEqual(env['OPENCODE_CONFIG_CONTENT'], '{}')
        for name in ('OPENCODE_CONFIG_PROJECT_DISABLE', 'OPENCODE_DISABLE_PROJECT_CONFIG',
                     'OPENCODE_DISABLE_CLAUDE_CODE', 'OPENCODE_DISABLE_CLAUDE_CODE_SKILLS'):
            self.assertEqual(env[name], '1')
        self.assertEqual(env['OPENCODE_CONFIG'], '{home}/' + CLIENT['mcp']['file'])

    def test_no_vault_key_or_offline_account_probe(self):
        for name in ('credentials', 'commands', 'permissions'):
            self.assertNotIn(name, MANIFEST)
        self.assertNotIn('key', CLIENT)
        self.assertNotIn('check', CLIENT['sign_in'])
        self.assertIn('ZAI_API_KEY', CLIENT['api_keys'])

    def test_behaviours_model_and_permission_mapping(self):
        self.assertEqual(CLIENT['instructions'], {'via': 'prompt'})
        self.assertEqual(CLIENT['mcp']['settings']['model'], 'zai-coding-plan/glm-5.3')
        permissions = CLIENT['run']['permissions']
        self.assertEqual(permissions['default'], ['--auto'])
        self.assertEqual(permissions['plan'], ['--agent', 'plan'])
        self.assertNotIn('--auto', permissions['plan'])

    def test_mcp_fixture_preserves_headers_and_argument_boundaries(self):
        f = json.loads((ROOT / 'tests/fixtures/mcp-contract.json').read_text())
        before, after = f['pointman_input'], f['opencode_expected']
        self.assertEqual(after['pointman']['type'], 'remote')
        self.assertFalse(after['pointman']['oauth'])
        self.assertEqual(after['pointman']['headers'], before['pointman']['headers'])
        self.assertEqual(after['pointman']['url'], before['pointman']['url'])
        local = before['local_example']
        self.assertEqual(after['local_example']['command'], [local['command'], *local['args']])
        self.assertEqual(after['local_example']['environment'], local['env'])
        self.assertEqual(CLIENT['mcp']['key'], 'mcp')

    def test_code_evidence_is_versioned_without_runtime_data(self):
        e = json.loads((ROOT / 'research/installed-evidence.json').read_text())
        self.assertEqual(e['version'], '2.2.1')
        self.assertEqual(len(e['sha256']), 64)
        self.assertIn('OPENCODE_DB', e['snippets']['database']['text'])
        self.assertIn('wellknown:sources', e['snippets']['remote-config']['text'])


class InstalledHelp(unittest.TestCase):
    def test_v2_help_in_synthetic_home(self):
        binary = os.environ.get('OPENCODE_CHECK_BINARY') or shutil.which('opencode')
        if not binary:
            self.skipTest('OpenCode not installed; static checks still run')
        with tempfile.TemporaryDirectory(prefix='opencode-contract-') as folder:
            root = Path(folder)
            env = {'PATH': os.defpath, 'HOME': folder, 'OPENCODE_DISABLE_MODELS_FETCH': '1'}
            for kind in ('DATA', 'CONFIG', 'CACHE', 'STATE'):
                env[f'XDG_{kind}_HOME'] = str(root / kind.lower())
            env.update({key: value.replace('{home}', folder)
                        for key, value in CLIENT['run']['env'].items()})
            def probe(*args):
                result = subprocess.run([binary, *args], cwd=folder, env=env,
                                        capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout
            self.assertIn('v2.2.1', probe('--version'))
            help_text = probe('run', '--help')
            for flag in ('--standalone', '--session', '--format', '--auto', '--model', '--agent'):
                self.assertIn(flag, help_text)
            self.assertIn('to create if it does not exist', help_text)


if __name__ == '__main__':
    unittest.main()
