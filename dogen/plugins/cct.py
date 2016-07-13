import os
import yaml
import subprocess
import shutil

from dogen.plugin import Plugin


class CCT(Plugin):
    @staticmethod
    def info():
        return "cct", "Support for configuring images via cct"

    def __init__(self, dogen):
        super(CCT, self).__init__(dogen)

    def prepare(self, cfg):
        """
        create cct changes yaml file for image.yaml template decscriptor
        it require cct aware template.jinja file
        """
        for module in self.find_modules(cfg['cct']['configure'][0]):
            project, module_name = module.split('.', 1)
            if project != 'base':
                repo_path = cfg['cct']['modules_repo']
                self.clone_repo(repo_path, project)
                try:
                    shutil.rmtree(self.output + '/cct')
                except:
                    pass # dir doesnt exists
                self.append_sources(project, cfg)
                os.makedirs(self.output + '/cct')
                shutil.copytree(project, self.output + '/cct/' + project)
                self.log.info("Cloned cct module %s." % project)
        cfg_file = os.path.join(self.output, "cct", "cct.yaml")
        cfg['cct']['run'] = ['cct.yaml']
        with open(cfg_file, 'w') as f:
            yaml.dump(cfg['cct']['configure'], f)

    def clone_repo(self, url, path):
        try:
            if not os.path.exists(path):
                subprocess.check_call(["git", "clone", url + path])
        except Exception as ex:
            self.log.error("cannot clone repo %s into %s: %s", url, path, ex)

    def find_modules(self, cct_config):
        repos = []
        for modules in cct_config['changes']:
            for module_name, ops in modules.items():
                repos.append(module_name)
        return repos

    def append_sources(self, module, cfg):
        sources_path = os.path.join(module, "sources.yaml")

        source_prefix = os.getenv("DOGEN_CCT_SOURCES_PREFIX")
        if source_prefix is None:
            source_prefix = ""
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