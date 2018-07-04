from ansiblelint import AnsibleLintRule

from ruamel.yaml import YAML  # cant use yaml/oyaml since ansiblelint overrides it's definition


def validate_hosts_declaration(declaration):
    keys = declaration.keys()
    declaration_errors = []

    print declaration

    if not keys[0] == 'hosts':
        declaration_errors.append(({'hosts': declaration['hosts']},
                                   '`hosts:` is not the first line in the declaration'))
    #
    # # pre_tasks, roles and tasks order
    # present_blocks = []
    #
    # if 'pre_tasks' in keys:
    #     present_blocks.append('pre_tasks')
    # if 'roles' in keys:
    #     present_blocks.append('roles')
    # if 'tasks' in keys:
    #     present_blocks.append('tasks')
    #
    # for i in xrange(len(present_blocks) - 1):
    #     former = keys.index(i)
    #     latter = keys.index(i+1)
    #
    #     if former > latter:
    #         former_key = present_blocks[i]
    #         latter_key = present_blocks[i+1]
    #         declaration_errors.append(({former_key: '...'},
    #                                    '%s should be declared before %s'.format(former_key,
    #                                                                             latter_key)))
    #
    # # host options alphabetical order check
    # first_block_idx = keys.index(present_blocks[0])
    #
    # for i in xrange(1, first_block_idx):
    #     former = keys[i]
    #     latter = keys[i+1]
    #
    #     if former > latter:
    #         declaration_errors.append(({former: declaration[former]},
    #                                    '%s should be declared before %s'.format(former,
    #                                                                             latter)))
    #
    # # make sure that the last present block of either 'pre_tasks', 'roles' or 'tasks'
    # # is the last key in the hosts declaration
    # last_block_idx = keys.index(present_blocks[-1])
    #
    # if last_block_idx != len(keys) - 1:
    #     last_key = keys[-1]
    #     declaration_errors.append(({last_key: '...'},
    #                                '%s should be declared last'.format(present_blocks[-1])))

    return declaration_errors


class HostsDeclaration(AnsibleLintRule):
    id = 'ANSIBLE-J0003'
    shortdesc = 'Hosts declaration should have a specific form.'
    description = 'Hosts declaration should use the following order: `hosts:` declaration, host options in alphabetical' \
                  'order, pre_tasks, roles, tasks.'
    tags = ['formatting']

    def matchplay(self, file, play):
        if file['type'] != 'playbook':
            return False

        path = file['path']

        results = []
        with open(path, 'r') as stream:
            yaml = YAML()
            for ordered_dict in yaml.load(stream):
                if 'hosts' in ordered_dict.keys():
                    results += validate_hosts_declaration(ordered_dict)
        print results
        return results
