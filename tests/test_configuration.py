"""Run with python3 -m unittest discover -s tests. No live firewall calls."""
import copy
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.settings = {
            'password_hash': 'unused-in-these-tests',
            'pfsense_url': 'https://firewall.example.org',
            'classrooms': [{'id': 1, 'name': 'Aula 1', 'tracker': '123', 'source': 'EQUIPOS'}],
        }
        folder = Path(cls.folder.name)
        (folder / 'settings.json').write_text(json.dumps(cls.settings))
        (folder / 'api-key').write_text('fake-test-key')
        (folder / 'session-key').write_text('fake-test-session-key')
        with patch.dict(os.environ, {'CONFIG_DIR': str(folder)}):
            cls.module = importlib.import_module('app')
        cls.module.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def setUp(self):
        self.saved = copy.deepcopy(self.module.CONFIG)
        self.module.CONFIG.clear()
        self.module.CONFIG.update(copy.deepcopy(self.settings))
        self.rule = dict(id=5, tracker=123, source='EQUIPOS', interface=['lan'],
                         type='block', destination='!Sare_pribatuak', ipprotocol='inet', disabled=True)
        self.client = self.module.app.test_client()

    def tearDown(self):
        self.module.CONFIG.clear()
        self.module.CONFIG.update(self.saved)

    def test_legacy_rule_keeps_exact_policy(self):
        self.module.validate_settings(self.module.CONFIG)
        self.assertIs(self.module.find_rule([self.rule], self.module.CONFIG['classrooms'][0]), self.rule)
        self.rule['destination'] = 'any'
        with self.assertRaises(self.module.FirewallError):
            self.module.find_rule([self.rule], self.module.CONFIG['classrooms'][0])

    def test_generic_and_per_classroom_criteria(self):
        classroom = self.module.CONFIG['classrooms'][0]
        self.module.CONFIG['firewall'] = {'interface': ['opt2'], 'destination': '!REDES_INTERNAS'}
        self.rule.update(interface=['opt2'], destination='!REDES_INTERNAS')
        self.module.find_rule([self.rule], classroom)
        classroom.update(interface=['opt3'], destination='!REDES_TALLER')
        with self.assertRaises(self.module.FirewallError):
            self.module.find_rule([self.rule], classroom)
        self.rule.update(interface=['opt3'], destination='!REDES_TALLER')
        self.module.find_rule([self.rule], classroom)
        for field, value in [('source', 'OTRA_AULA'), ('type', 'pass'), ('ipprotocol', 'inet6'), ('disabled', 'true')]:
            with self.subTest(field=field):
                bad = dict(self.rule, **{field: value})
                with self.assertRaises(self.module.FirewallError):
                    self.module.find_rule([bad], classroom)

    def test_ambiguous_or_incomplete_classrooms_rejected(self):
        for changed in [
            [dict(self.settings['classrooms'][0]), dict(self.settings['classrooms'][0])],
            [{'id': 1, 'name': 'Taller', 'tracker': '123'}],
            [{'id': '1', 'name': 'Taller', 'tracker': None}],
            [{'id': 1, 'name': 'Taller', 'tracker': None, 'interface': 'lan'}],
        ]:
            with self.subTest(classrooms=changed):
                with self.assertRaises(ValueError):
                    self.module.validate_settings(dict(self.settings, classrooms=changed))

    def test_brand_is_configured_and_escaped_on_login_and_panel(self):
        self.module.CONFIG['center_name'] = 'Centro <Prueba>'
        login = self.client.get('/login', base_url='https://localhost').get_data(as_text=True)
        self.assertIn('Centro &lt;Prueba&gt;', login)
        with self.client.session_transaction() as session:
            session['authenticated'] = True
        page = self.client.get('/', base_url='https://localhost').get_data(as_text=True)
        self.assertIn('Centro &lt;Prueba&gt;', page)
        self.assertNotIn('class="brand">CEINPRO', page)

    def test_euskera_custom_name_and_unconfigured_classroom(self):
        self.module.CONFIG['classrooms'] = [dict(id=7, name='Taller', name_eu='Tailerra', tracker=None)]
        self.client.set_cookie('language', 'eu')
        with self.client.session_transaction() as session:
            session['authenticated'] = True
        page = self.client.get('/', base_url='https://localhost').get_data(as_text=True)
        self.assertIn('Tailerra', page)
        self.assertIn('data-id="7"', page)
        with patch.object(self.module, 'firewall', side_effect=[[], {'applied': True}]):
            response = self.client.get('/api/status', base_url='https://localhost')
        self.assertEqual(response.json['classrooms'], [{'id': 7, 'state': 'unconfigured'}])

    def test_default_brand_for_old_settings(self):
        page = self.client.get('/login', base_url='https://localhost').get_data(as_text=True)
        self.assertIn('Centro educativo', page)


class InstallerTests(unittest.TestCase):
    def test_installer_saves_site_settings_without_linking_foreign_rules(self):
        import setup
        saved_cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                answers = ['Centro de ejemplo', 'https://firewall.example.org', 'panel.example.org',
                           '127.0.0.1', '9445', '2', 'opt2', 'REDES_LOCALES', '']
                with (patch.object(setup, '__file__', str(root / 'setup.py')),
                      patch('builtins.input', side_effect=answers),
                      patch.object(setup.getpass, 'getpass', side_effect=['test-key', 'test-password-long', 'test-password-long']),
                      patch.object(setup.urllib.request, 'urlopen') as urlopen,
                      patch.object(setup.subprocess, 'run') as openssl,
                      patch.object(setup.os, 'chown')):
                    urlopen.return_value.__enter__.return_value.read.return_value = b'{"status":"ok","data":[]}'
                    setup.main()
                config = json.loads((root / 'config/settings.json').read_text())
                self.assertEqual(config['center_name'], 'Centro de ejemplo')
                self.assertEqual(config['firewall'], {'interface': ['opt2'], 'destination': '!REDES_LOCALES'})
                self.assertEqual(len(config['classrooms']), 2)
                self.assertTrue(all(c['tracker'] is None for c in config['classrooms']))
                self.assertIn('PANEL_PORT=9445', (root / '.env').read_text())
                self.assertIn('subjectAltName=DNS:panel.example.org', openssl.call_args.args[0])
                from werkzeug.security import check_password_hash
                self.assertTrue(check_password_hash(config['password_hash'], 'test-password-long'))
                with patch.object(setup, '__file__', str(root / 'setup.py')):
                    with self.assertRaises(SystemExit):
                        setup.main()
        finally:
            os.chdir(saved_cwd)


if __name__ == '__main__':
    unittest.main()
