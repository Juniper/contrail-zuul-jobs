import os
import re

from ansible.module_utils.basic import AnsibleModule
from datetime import datetime

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

result = dict(
    changed=False,
    original_message='',
    message='',
)

version_branch_regex = re.compile(r'^(master)|(R\d+\.\d+(\.\d+)?(\.x)?)$')

next_release = {
    'R5.0': '5.0.3',
    'master': '5.1.0'
}

class ReleaseType(object):
    CONTINUOUS_INTEGRATION = 'continuous-integration'
    NIGHTLY = 'nightly'


def main():
    module = AnsibleModule(
        argument_spec=dict(
            zuul=dict(type='dict', required=True),
            release_type=dict(type='str', required=False, default=ReleaseType.CONTINUOUS_INTEGRATION),
            build_number=dict(type='str', required=False, default=''),
            openstack_version=dict(type='str', required=False, default='')
        )
    )

    zuul = module.params['zuul']
    release_type = module.params['release_type']
    build_number = module.params['build_number']
    openstack_version = module.params['openstack_version']

    branch = zuul['branch']
    release = next_release.get(branch, next_release['master'])
    date = datetime.now().strftime("%Y%m%d%H%M%S")

    if release_type == ReleaseType.CONTINUOUS_INTEGRATION:
        # Versioning in CI consists of change id, pachset and date
        change = zuul['change']
        patchset = zuul['patchset']
        build = patchset + '.' + change
    elif release_type == ReleaseType.NIGHTLY:
        build = '0.' + str(build_number)
    else:
        module.fail_json(
            msg="Unknown release_type: %s" % (release_type,), **result
        )
    tag = release + '-' + build

    target_dir = 'contrail-' + release

    openstack_suffix = ('-' + openstack_version) if openstack_version else ''
    repo_names = {
        "CentOS": tag + '-centos',
        "RedHat": tag + '-rhel' + openstack_suffix,
    }

    docker_tags = {
        "CentOS": tag,
        "RedHat": tag + '-rhel'
    }

    openstack_specific_docker_tags = { k: v + openstack_suffix for k,v in docker_tags.items() }

    packaging = {
        'version': version,
        'release': release,
        'build': build,
        'tag': tag,
        'target_dir': target_dir,
        'repo_names': repo_names,
        'docker_tags': docker_tags,
        'openstack_specific_docker_tags': openstack_specific_docker_tags
    }

    module.exit_json(ansible_facts={'packaging': packaging}, **result)


if __name__ == "__main__":
    main()
