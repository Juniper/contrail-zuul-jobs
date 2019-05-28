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

MASTER_RELEASE = '5.1.0'
version_branch_regex = re.compile(r'^(master)|(R\d+\.\d+(\.\d+)?(\.x)?)$')


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
    if not version_branch_regex.match(branch):
        branch = 'master'
    date = datetime.now().strftime("%Y%m%d%H%M%S")

    version = {'epoch': None}
    if branch == 'master':
        version['upstream'] = MASTER_RELEASE
        version['public'] = 'master'
        docker_version = 'master'
    else:
        version['upstream'] = branch[1:]
        version['public'] = branch[1:]
        docker_version = version['upstream']

    if release_type == ReleaseType.CONTINUOUS_INTEGRATION:
        # Versioning in CI consists of change id, pachset and date
        change = zuul['change']
        patchset = zuul['patchset']
        version['distrib'] = "ci{change}.{patchset}".format(
            change=change, patchset=patchset, date=date
        )
        docker_version = "{change}-{patchset}".format(change=change, patchset=patchset)
    elif release_type == ReleaseType.NIGHTLY:
        version['distrib'] = "{}".format(build_number)
        docker_version = '{}-{}'.format(docker_version, build_number)
    else:
        module.fail_json(
            msg="Unknown release_type: %s" % (release_type,), **result
        )

    repo_name = docker_version

    debian_dir = None
    for project in zuul['projects']:
        if project['short_name'] in ["contrail-packages", "packages"]:
            debian_dir = os.path.join(project['src_dir'], "debian/contrail/debian")

    target_dir = "contrail-%s" % (version['upstream'],)

    full_version = "{upstream}~{distrib}".format(**version)

    openstack_suffix = ('-' + openstack_version) if openstack_version else ''
    repo_names = {
        "CentOS": repo_name + '-centos',
        "RedHat": repo_name + '-rhel' + openstack_suffix,
    }

    packaging = {
        'name': 'contrail',
        'debian_dir': debian_dir,
        'full_version': full_version,
        'version': version,
        'target_dir': target_dir,
        'repo_name': repo_name,
        'repo_names': repo_names,
        'docker_version': docker_version,
    }

    module.exit_json(ansible_facts={'packaging': packaging}, **result)


if __name__ == "__main__":
    main()
