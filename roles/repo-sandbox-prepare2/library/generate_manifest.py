#!/usr/bin/env python
from __future__ import print_function

ANSIBLE_METADATA = {
        'metadata_version': '1.1',
        'status': ['preview'],
        'supported_by': 'community'
}

import os
import subprocess

from lxml import etree

from ansible.module_utils.basic import AnsibleModule


def get_head_commit_sha(path):
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path)
    return sha[:-1]


def get_head_branch(path):
    """Return the git ref that is currently checked-out in the working copy
    at path"""
    head = subprocess.check_output(['git', 'symbolic-ref', 'HEAD'], cwd=path)
    return head[:-1]


def dump_xml(node):
    return etree.tostring(node, pretty_print=True).decode()


def del_node(node):
    node.getparent().remove(node)


def get_project(projects, short_name):
    for project, data in projects.items():
        if data['short_name'] == short_name:
            return data
    msg = "Zuul does not know about project {}.\n".format(short_name)
    msg += "Make sure it is defined in ``required-projects'' for this job."
    raise RuntimeError(msg)


def convert_to_valid_git_id(dirname):
    return dirname.replace('/', '--')


def translate(zuul_projects, sandbox_root, manifest_path):
    """This will rewrite manifest to fetch repositories from filesystem locations
    instead of GitHub URLs. This way zuul-merger-prepared checkouts can be used
    during `repo sync`
    """
    with open(manifest_path, 'r') as manifest_file:
        manifest = etree.parse(manifest_file)

    for remote in manifest.xpath('//remote'):
        del_node(remote)

    for default in manifest.xpath('//default'):
        del_node(default)

    remotes = {}
    for zuul_project in zuul_projects.values():
        parent_dir = os.path.dirname(zuul_project['src_dir'])
        remote_name = convert_to_valid_git_id(parent_dir)
        absolute_parent_url = 'file://{}/{}'.format(os.environ['HOME'], parent_dir)
        remotes[remote_name] = etree.Element(
            'remote',
            name=remote_name,
            fetch=absolute_parent_url
        )
        remotes[remote_name].tail = '\n'

    for remote in remotes.values():
        manifest.getroot().insert(0, remote)

    # A mapping between sandbox project paths and their remotes, this
    # can be used later in ansible to re-create origin remotes so that
    # a review diff can be generated.
    origins = {}
    for project in manifest.xpath('//project'):
        name = project.attrib['name']
        zuul_project = get_project(zuul_projects, name)
        remote_name = convert_to_valid_git_id(os.path.dirname(zuul_project['src_dir']))
        project.attrib['remote'] = remote_name
        head = get_head_branch(
            os.path.join(os.environ['HOME'], zuul_project['src_dir'])
        )
        project.attrib['revision'] = head
        try:
            project_relative_path = project.attrib['path']
        except KeyError:
            project_relative_path = project.attrib['name']
        sandbox_path = os.path.join(sandbox_root, project_relative_path)
        origins[sandbox_path] = "https://%s" % (zuul_project['canonical_name'],)

    return dump_xml(manifest), origins


def snapshot(projects, manifest_path):
    """ This will rewrite manifest by adding git commit SHAs to each project
    in the "revision" attribute. This is for preserving the information about
    the exact code version used during the build
    """
    with open(manifest_path, 'r') as manifest_file:
        manifest = etree.parse(manifest_file)

    for project in manifest.xpath('//project'):
        name = project.attrib['name']
        zuul_project = get_project(projects, name)
        sha = get_head_commit_sha(
            os.path.join(
                os.environ['HOME'],
                zuul_project['src_dir']))
        project.attrib['revision'] = sha
    return dump_xml(manifest)


def run_module():
    module_args = dict(
        manifest_path=dict(type='str', required=True),
        projects=dict(type='dict', required=True),
        sandbox_root=dict(type='str', required=True),
        snapshot_path=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    projects = module.params['projects']
    manifest_path = module.params['manifest_path']
    sandbox_root = module.params['sandbox_root']
    snapshot_path = module.params['snapshot_path']

    translated_manifest, origins = translate(projects, sandbox_root,
                                             manifest_path)
    translated_path = os.path.join(sandbox_root, ".repo/manifest.xml")
    with open(translated_path, 'w') as fh:
        fh.write(translated_manifest)

    snapshot_manifest = snapshot(projects, manifest_path)
    with open(snapshot_path, 'w') as fh:
        fh.write(snapshot_manifest)

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module.exit_json(ansible_facts={'origins': origins}, **result)

def main():
    run_module()

if __name__ == '__main__':
    main()

