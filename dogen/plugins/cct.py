import os
import yaml
import subprocess
import shutil
import tempfile

from dogen.plugin import Plugin


class CCT(Plugin):
    @staticmethod
    def info():
        return "cct", "Support for configuring images via cct"

    def __init__(self, dogen):
        super(CCT, self).__init__(dogen)
        self._setup_working_dir()

# HANG ON. think. do the things we're putting in here need to be around at
# Docker build time? Probably? Extra CCT modules etc., surely?

    def _setup_working_dir(self):
        """
        Create a temporary working directory within which we can write things
        which might include clones of remote module repositories, temporary
        files, etc.
        """
        self.wdir = tempfile.mkdtemp(prefix='dogen-cct.')

    def prepare(self, cfg):
        """
        create cct changes yaml file for image.yaml template descriptor
        """
        modules = cfg['cct']['configure']

        for module in self.find_module_names(modules):

            # modules names must be e.g. base.Shell, foo.Bar
            project, module_name = module.split('.', 1)

            if project != 'base':
                repo_path = cfg['cct']['modules_repo']

                repo_dest = os.path.join(self.wdir, path)
                self._clone_repo(repo_path + project, repo_dest)

                # Clean up possibly stale outputs from prior runs
                with self.output + "/cct" as path:
                    if os.path.exists(path):
                        shutil.rmtree(path)

                self.append_sources(project, cfg) # ???
                os.makedirs(self.output + '/cct')
                shutil.copytree(repo_dest, self.output + '/cct/' + project)
                self.log.info("Cloned cct module %s." % project)

        cfg_file = os.path.join(self.output, "cct", "cct.yaml")
        cfg['cct']['run'] = ['cct.yaml']
        with open(cfg_file, 'w') as f:
            yaml.dump(cfg['cct']['configure'], f)

    def _clone_repo(self, url, path):
        """
        Clone a git repository from url to local path
        """
        try:
            if not os.path.exists(path):
                subprocess.check_output(["git", "clone", url, path])
        except Exception as ex:
            self.log.error("cannot clone repo %s into %s: %s", url, path, ex)
            self.log.error(ex.output)

    def find_module_names(self, cct_config):
        """
        given a YAML snippet cct_config, extract a list of module names

        """
        repos = []
        for modules in cct_config['changes']:
            for module_name, ops in modules.items():
                repos.append(module_name)
        return repos

    def append_sources(self, module, cfg):
        """
        Read in source file descriptions from sources.yaml, modify
        them according to DOGEN_CCT_SOURCES_PREFIX if provided, and
        add the result to Dogen's sources list
        """
        sources_path = os.path.join(self.wdir, module, "sources.yaml")

        source_prefix = os.getenv("DOGEN_CCT_SOURCES_PREFIX") or ""
        if not source_prefix:
            self.log.debug("DOGEN_CCT_SOURCES_PREFIX variable is not provided")

        with open(sources_path) as f:
            cct_sources = yaml.load(f)

            dogen_sources = []
            for source in cct_sources:
                dogen_source = {}
                dogen_source['url'] = source_prefix + source['name']
                print dogen_source['url']
                dogen_source['hash'] = source['chksum']
                dogen_sources.append(dogen_source)
            try:
                cfg['sources'].extend(dogen_sources)
            except:
                cfg['sources'] = dogen_sources
