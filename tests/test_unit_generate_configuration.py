import unittest
import mock
import six
import tarfile
import os
import tempfile

from dogen.generator import Generator
from dogen.errors import Error
from dogen import version, DEFAULT_SCRIPT_EXEC, DEFAULT_SCRIPT_USER

class TestConfig(unittest.TestCase):

    # keys that must be present in config file but we don't care about
    # for specific tests
    basic_config ="release: '1'\nversion: '1'\ncmd:\n - whoami\nfrom: scratch\nname: someimage\n"

    def setUp(self):
        self.log = mock.Mock()
        self.descriptor = tempfile.NamedTemporaryFile(delete=False)
        self.descriptor.write(self.basic_config.encode())

    def tearDown(self):
        os.remove(self.descriptor.name)

    def test_default_values(self):
        self.generator = Generator(self.log, self.descriptor.name, "target")
        self.assertEqual(self.generator.output, "target")
        self.assertEqual(self.generator.dockerfile, "target/Dockerfile")
        self.assertEqual(self.generator.descriptor, self.descriptor.name)
        self.assertEqual(self.generator.template, None)
        self.assertEqual(self.generator.scripts_path, None)
        self.assertEqual(self.generator.additional_scripts, None)
        self.assertEqual(self.generator.without_sources, False)
        # Set to True in the configure() method later 
        self.assertEqual(self.generator.ssl_verify, None)

    def test_fail_if_version_mismatch(self):
        with self.descriptor as f:
            f.write("dogen:\n  version: 99999.9.9-dev1".encode())

        self.generator = Generator(self.log, self.descriptor.name, "target")

        with self.assertRaises(Error) as cm:
            self.generator.configure()

        self.assertEquals(
            str(cm.exception), "You try to parse descriptor that requires Dogen version 99999.9.9-dev1, but you run version %s" % version)

    def test_skip_ssl_verification_in_descriptor(self):
        with self.descriptor as f:
            f.write("dogen:\n  ssl_verify: false".encode())

        generator = Generator(self.log, self.descriptor.name, "target")
        generator.configure()
        self.assertFalse(generator.ssl_verify)

    def test_do_not_skip_ssl_verification_in_descriptor(self):
        with self.descriptor as f:
            f.write("dogen:\n  ssl_verify: true".encode())

        generator = Generator(self.log, self.descriptor.name, "target")
        generator.configure()
        self.assertTrue(generator.ssl_verify)

    def test_custom_template_in_descriptor(self):
        with self.descriptor as f:
            f.write("dogen:\n  template: custom-template.jinja".encode())

        generator = Generator(self.log, self.descriptor.name, "target")
        generator.configure()
        self.assertEqual(generator.template, "custom-template.jinja")

    def test_custom_template_in_cli_should_override_in_descriptor(self):
        with self.descriptor as f:
            f.write("dogen:\n  template: custom-template.jinja".encode())

        generator = Generator(self.log, self.descriptor.name, "target", template="cli-template.jinja")
        generator.configure()
        self.assertEqual(generator.template, "cli-template.jinja")

    def test_do_not_skip_ssl_verification_in_cli_true_should_override_descriptor(self):
        with self.descriptor as f:
            f.write("dogen:\n  ssl_verify: false".encode())

        generator = Generator(self.log, self.descriptor.name, "target", ssl_verify=True)
        generator.configure()
        self.assertTrue(generator.ssl_verify)

    def test_do_not_skip_ssl_verification_in_cli_false_should_override_descriptor(self):
        with self.descriptor as f:
            f.write("dogen:\n  ssl_verify: true".encode())

        generator = Generator(self.log, self.descriptor.name, "target", ssl_verify=False)
        generator.configure()
        self.assertFalse(generator.ssl_verify)

    @mock.patch('dogen.generator.os.path.exists', return_value=True)
    def test_custom_scripts_dir_in_descriptor(self, mock_patch):
        with self.descriptor as f:
            f.write("dogen:\n  scripts_path: custom-scripts".encode())

        generator = Generator(self.log, self.descriptor.name, "target")
        generator.configure()
        mock_patch.assert_called_with('custom-scripts')
        self.assertEqual(generator.scripts_path, "custom-scripts")

    @mock.patch('dogen.generator.os.path.exists', return_value=True)
    def test_custom_scripts_dir_in_cli_should_override_in_descriptor(self, mock_patch):
        with self.descriptor as f:
            f.write("dogen:\n  template: custom-scripts".encode())

        generator = Generator(self.log, self.descriptor.name, "target", scripts_path="custom-scripts-cli")
        generator.configure()
        mock_patch.assert_called_with('custom-scripts-cli')
        self.assertEqual(generator.scripts_path, "custom-scripts-cli")

    @mock.patch('dogen.generator.os.path.exists', return_value=True)
    def test_scripts_dir_found_by_convention(self, mock_patch):
        with self.descriptor as f:
            f.write("dogen:\n  scripts_path: custom-scripts".encode())

        generator = Generator(self.log, self.descriptor.name, "target")
        generator.configure()
        mock_patch.assert_called_with('custom-scripts')
        self.assertEqual(generator.scripts_path, "custom-scripts")

    def test_custom_additional_scripts_in_descriptor(self):
        with self.descriptor as f:
            f.write("dogen:\n  additional_scripts:\n    - http://host/somescript".encode())

        generator = Generator(self.log, self.descriptor.name, "target")
        generator.configure()
        self.assertEqual(generator.additional_scripts, ["http://host/somescript"])

    def test_custom_additional_scripts_in_cli_should_override_in_descriptor(self):
        with self.descriptor as f:
            f.write("dogen:\n  additional_scripts:\n    - http://host/somescript".encode())

        generator = Generator(self.log, self.descriptor.name, "target", additional_scripts=["https://otherhost/otherscript"])
        generator.configure()
        self.assertEqual(generator.additional_scripts, ["https://otherhost/otherscript"])

    @mock.patch('dogen.generator.os.path.exists', return_value=True)
    def helper_test_script_exec(self, exec_to_test, cfg, mock_patch):
        """Helper method for tests around script exec value"""
        with self.descriptor as f:
            f.write(cfg.encode())

        generator = Generator(self.log, self.descriptor.name, "target", scripts_path="scripts")
        generator.configure()
        generator._handle_scripts()
        self.assertEqual(generator.cfg['scripts'][0]['exec'], exec_to_test)

    def test_default_script_exec(self):
        """Ensure that when no 'exec' is defined for a script and DOGEN_SCRIPT_EXEC is
           unset, the default is used."""

        os.environ.pop('DOGEN_SCRIPT_EXEC', None)

        cfg = self.basic_config + "scripts:\n    - package: somepackage"

        self.helper_test_script_exec(DEFAULT_SCRIPT_EXEC, cfg)

    def test_env_supplied_script_exec(self):
        """Ensure that when no 'exec' is defined for a script and DOGEN_SCRIPT_EXEC is defined,
           DOGEN_SCRIPT_EXEC is used."""

        custom_script_name = "somescript.sh"
        # we must be sure that DEFAULT_SCRIPT_EXEC is not being used by accident
        self.assertNotEqual(custom_script_name, DEFAULT_SCRIPT_EXEC)
        os.environ['DOGEN_SCRIPT_EXEC'] = custom_script_name
        cfg = self.basic_config + "scripts:\n    - package: somepackage"

        self.helper_test_script_exec(custom_script_name, cfg)

    def test_custom_script_exec(self):
        """Ensure that when 'exec' *is* defined for a script and DOGEN_SCRIPT_EXEC is
           not defined, exec is used and not the default."""

        os.environ.pop('DOGEN_SCRIPT_EXEC', None)
        custom_script_name = "somescript.sh"
        self.assertNotEqual(custom_script_name, DEFAULT_SCRIPT_EXEC)
        cfg = self.basic_config + "scripts:\n  - package: somepackage\n    exec: " + custom_script_name

        self.helper_test_script_exec(custom_script_name, cfg)

    def test_custom_script_exec_not_env(self):
        """Ensure that when 'exec' *is* defined for a script, it is not overridden by a
           provided value in the environment, or the default."""

        os.environ['DOGEN_SCRIPT_EXEC'] = "some_other_script.sh"
        custom_script_name = "somescript.sh"
        self.assertNotEqual(custom_script_name, DEFAULT_SCRIPT_EXEC)
        cfg = self.basic_config + "scripts:\n  - package: somepackage\n    exec: " + custom_script_name

        self.helper_test_script_exec(custom_script_name, cfg)

    @mock.patch('dogen.generator.os.path.exists', return_value=True)
    def helper_test_script_user(self, cfg, user_to_test, mock_patch):
        """A helper for script user-related tests"""

        with self.descriptor as f:
            f.write(cfg.encode())

        generator = Generator(self.log, self.descriptor.name, "target", scripts_path="scripts")
        generator.configure()
        generator._handle_scripts()
        self.assertEqual(generator.cfg['scripts'][0]['user'], user_to_test)

    def test_default_script_user(self):
        """Ensure that when no 'user' is defined for a script and DOGEN_DEFAULT_USER is unset,
           the default is used."""

        os.environ.pop('DOGEN_SCRIPT_USER', None)
        cfg = self.basic_config + "scripts:\n    - package: somepackage"

        self.helper_test_script_user(cfg, DEFAULT_SCRIPT_USER)

    def test_env_provided_script_user(self):
        """Ensure that when no 'user' is defined for a script and DOGEN_DEFAULT_USER is set,
           DOGEN_SCRIPT_USER is used."""

        env_user = os.environ['DOGEN_SCRIPT_USER'] = 'some_user'
        self.assertNotEqual(env_user, DEFAULT_SCRIPT_USER)
        cfg = self.basic_config + "scripts:\n    - package: somepackage"

        self.helper_test_script_user(cfg, env_user)

    def test_custom_script_user_not_default(self):
        """Ensure that when 'user' *is* defined for a script and DOGEN_SCRIPT_USER is not set,
           the script user is used."""

        os.environ.pop('DOGEN_SCRIPT_USER', None)
        custom_script_user = "notroot"
        self.assertNotEqual(custom_script_user, DEFAULT_SCRIPT_USER)
        cfg = self.basic_config + "scripts:\n  - package: somepackage\n    user: " + custom_script_user

        self.helper_test_script_user(cfg, custom_script_user)

    def test_custom_script_user_not_env(self):
        """Ensure that when 'user' *is* defined for a script and DOGEN_SCRIPT_USER is set,
           the script user is used."""

        custom_script_user = "notroot"
        env_user = "nobody"
        self.assertNotEqual(custom_script_user, DEFAULT_SCRIPT_USER)
        self.assertNotEqual(env_user, DEFAULT_SCRIPT_USER)
        os.environ['DOGEN_SCRIPT_USER'] = env_user
        cfg = self.basic_config + "scripts:\n  - package: somepackage\n    user: " + custom_script_user

        self.helper_test_script_user(cfg, custom_script_user)

    def test_no_scripts_defined(self):
        "make sure _handle_scripts doesn't blow up when there are no scripts"

        self.descriptor.close()
        generator = Generator(self.log, self.descriptor.name, "target", scripts_path="scripts")
        generator.configure()
        generator._handle_scripts()
        # success if no stack trace thrown
