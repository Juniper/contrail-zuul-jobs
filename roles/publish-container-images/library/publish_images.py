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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            images=dict(type='dict', required=True),
            registry=dict(type='str', required=True),
        )
    )
    p = module.params

    # We import docker here, to provide a useful message back
    # to ansible in case the import fails.
    try:
        import docker
    except ImportError as e:
        module.fail_json(msg="Couldn't import docker package: %s" % (str(e),), **result)

    client = docker.from_env()

    images = []
    for i in p['images']:
        try:
            image_name = ":".join((i['name'], i['tag']))
            i = client.get(image_name)
        except docker.errors.ImageNotFound:
            module.fail_json(
                msg="Missing image: %s" % (image_name,),
                **result)
        images += i

    for image in images:
        image.push(p['registry'], tag=p['tag'])

    module.exit_json(**result)


if __name__ == "__main__":
    main()
