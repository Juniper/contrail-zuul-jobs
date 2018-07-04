from ansiblelint import AnsibleLintRule

from ruamel.yaml import YAML  # cant use yaml/oyaml since ansiblelint overrides it's definition


def validate_hosts_declaration(declaration):
    keys = declaration.keys()
    declaration_errors = []

    if not keys[0] == 'hosts':
        declaration_errors.append(({'hosts': declaration['hosts']},
                                   '`hosts:` is not the first line in the declaration'))

    # pre_tasks, roles and tasks order
    present_blocks = []

    if 'pre_tasks' in keys:
        present_blocks.append('pre_tasks')
    if 'roles' in keys:
        present_blocks.append('roles')
    if 'tasks' in keys:
        present_blocks.append('tasks')

    for i in xrange(len(present_blocks) - 1):
        former_key = present_blocks[i]
        latter_key = present_blocks[i+1]

        former_pos = keys.index(former_key)
        latter_pos = keys.index(latter_key)

        if former_pos > latter_pos:
            declaration_errors.append(({former_key: '...'},
                                       '{} should be declared before {}'.format(former_key,
                                                                                latter_key)))

    # host options alphabetical order check
    options = [opt for opt in keys if opt not in (present_blocks + ['name', 'hosts'])]

    for i in xrange(len(options) - 1):
        former = options[i]
        latter = options[i+1]

        if former > latter:
            declaration_errors.append(({former: '...'},
                                       '{} should be declared after {}'.format(former,
                                                                                latter)))

    # make sure that the last present blocks are 'pre_tasks', 'roles' or 'tasks'
    if not set(present_blocks) == set(keys[-len(present_blocks):]):
        declaration_errors.append(({present_blocks[-1]: '...'},
                                   '{} should be declared last'.format(','.join(present_blocks))))

    return declaration_errors


def get_ordered_play_from_file(play, file):
    play_start_line_no = play['__line__'] - 1

    with open(file['path'], 'r') as _file:
        content = _file.readlines()

    play_end_line_no = play_start_line_no + 1
    while not content[play_end_line_no].startswith('-') and play_end_line_no < len(content) - 1:
        play_end_line_no += 1

    play_to_parse = content[play_start_line_no:play_end_line_no]

    yaml = YAML()

    return yaml.load(''.join(play_to_parse))[0]


class HostsDeclaration(AnsibleLintRule):
    id = 'ANSIBLE-J0003'
    shortdesc = 'Hosts declaration should have a specific form.'
    description = 'Hosts declaration should use the following order: `hosts:` declaration, host options in alphabetical' \
                  'order, pre_tasks, roles, tasks.'
    tags = ['formatting']

    def matchplay(self, file, play):
        if file['type'] != 'playbook':
            return False

        results = []

        if 'hosts' in play.keys():
            ordered_dict = get_ordered_play_from_file(play, file)
            results += validate_hosts_declaration(ordered_dict)

        return results
