from rxjson import Rx
import yaml

rx = Rx.Factory({ "register_core_types": True })

# required: name: release: from: labels: envs: ports: cmd:
# XXX: This covers fields accessed in the Python *and* in the default template,
# but the default template can be overridden
cct_schema = """
type: //rec
required:
  name: {type: //str}
  from: {type: //str}
  version: {type: //str}
  release: {type: //str}
  cmd:
    type: //arr
    contents: {type: //str}
optional:
  openshift: {type: //bool}
  labels:
    type: //arr
    contents:
      type: //rec
      required:
        name: {type: //str}
        value: {type: //str}
      optional:
        description: {type: //str}
  envs:
    type: //rec
    optional:
      information:
        type: //arr
        contents:
          type: //rec
          required:
            name: {type: //str}
            value: {type: //str}
          optional:
            description: {type: //str}
      configuration:
        type: //arr
        contents:
          type: //rec
          required:
            name: {type: //str}
            example: {type: //str}
          optional:
            description: {type: //str}
  ports:
    type: //arr
    contents:
      type: //rec
      required:
        value: //int
  debugport: {type: //int}
  dogen:
    type: //rec
    optional:
      version: {type: //str}
      ssl_verify: {type: //bool}
      template: {type: //str}
      scripts: {type: //str}
      additional_scripts: {type: //str}
  verbose: {type: //int}
  maintainer: {type: //str}
  sources:
    type: //arr
    contents:
      type: //rec
      required:
        url: {type: //str}
        hash: {type: //str}
"""

cct ="""
name: "jboss-eap-7/eap70"
from: "jboss-base-7/jdk8:1.2"
version: "1.2"
release: "dev"
openshift: false
cmd:
  - "zomg"
  - "lol"
labels:
  - name: mylabel
    value: zomg
    description: just a stupid example
envs:
  information:
    - name: "LAUNCH_JBOSS_IN_BACKGROUND"
      value: "true"
    - name: "JBOSS_PRODUCT"
      value: o yeah
  configuration:
    - name: "DEBUG"
      example: "true"
      description: "Specify true to enable development mode (debugging)."
ports:
  - value: 8080
debugport: 8787
dogen:
  scripts: "zomg"
maintainer: jdowland@redhat
sources:
  - url: redmars.org
    hash: 1337x
"""

cct_schema = yaml.load(cct_schema)
cct = yaml.load(cct)

print rx.make_schema(cct_schema).check(cct)
