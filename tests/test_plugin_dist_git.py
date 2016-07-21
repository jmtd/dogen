import unittest
import mock
import six
import os
import tempfile

from dogen.generator import Generator
from dogen.plugins.dist_git import DistGitPlugin, Git

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.log = mock.Mock()
        #self.plugin = DistGitPlugin()
        self.git = Git(log=self.log, source='.', path='.')

    def tearDown(self):
        pass

    def test_zomg(self):
        # XXX: dangerous - the git module calls 'reset --hard' in one routine: we need to
        # clone a sacrificial lamb repo, check out a known ref, and run tests with that.
        self.assertEqual(self.git.source_repo_name, "dogen")
        self.assertEqual(self.git.source_repo_branch, "plugins-fixtests")
        self.assertEqual(self.git.source_repo_commit, "756f42e5518cf8aa790b837544a6719c8038c5f8")
        pass
