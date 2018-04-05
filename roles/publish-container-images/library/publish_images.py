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
    message='',
)

def get_image(client, full_name):
    images = client.images()
    for i in images:
        if full_name in i['RepoTags']:
            return i
    return None

def main():
    module = AnsibleModule(
        argument_spec=dict(
            images=dict(type='list', required=True),
            tag=dict(type='str', required=True),
            registry=dict(type='str', required=True),
        )
    )
    params = module.params

    # We import docker here, to provide a useful message back
    # to ansible in case the import fails.
    try:
        import docker
    except ImportError as e:
        module.fail_json(msg="Couldn't import docker package: %s" % (str(e),), **result)

    client = docker.from_env()

    images = []
    for i in params['images']:
        image_name = ":".join((i['name'], i['tag']))
        repository = "/".join((params['registry'], i['name']))
        try:
            client.tag(image_name, repository=repository, tag=params['tag'])
        except docker.errors.NotFound:
            module.fail_json(
                msg="Missing local image: %s" % (image_name,), **result)
        except Exception as e:
            module.fail_json(
                msg="Unknown error while tagging %s for registry %s: %s" % (
                    image_name, repository, str(e))
            )
        images += [repository]

    image_verbose = {}
    for image_repository in images:
        try:
            response = [line for line in client.push(image_repository, tag=params['tag'], insecure_registry=True, stream=True)]
        except Exception as e:
            msg = "Unknown error while pushing %s: %s" % (
                ":".join((image_repository, params['tag'])), str(e),
            )
            module.fail_json(msg=msg, **result)
    image_verbose[image_repository] = response

    result['verbose'] = image_verbose
    if len(params['images']) > 0:
        result['changed'] = True

    module.exit_json(msg="Uploaded the following images: %s with a tag %s" % (", ".join(images), params['tag']),**result)


if __name__ == "__main__":
    main()
