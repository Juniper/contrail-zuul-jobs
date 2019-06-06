from ansiblelint import AnsibleLintRule
import re


class TasksDeclaration(AnsibleLintRule):
    id = 'ANSIBLE-J0004'
    shortdesc = 'Tasks declaration should have a specific form.'
    description = 'N/A'
    tags = ['formatting']

    def check_tasks_name(self, file, play):
        declaration_errors = []
        for task in play['tasks']:
            task_name = task['name']
            if not task_name.islower():
                declaration_errors.append(({task_name: '...'},
                                           'Line: {} - Task name: "{}" - should start with lowercase!'.format(
                                               task['__line__'], task_name)))
        return declaration_errors

    def space_tasks(self, file, play):
        declaration_errors = []
        pattern = re.compile("\w+\:\w+")
        for i, line in enumerate(open(file['path'], 'r')):
            for math in re.findall(pattern, line):
                declaration_errors.append(({line: '...'}, 'Line: {} - should be space after :'.format(line)))
        return declaration_errors

    def matchplay(self, file, play):
        result = []
        if file['type'] != 'playbook':
            return False
        if 'tasks' in play:
            result += self.check_tasks_name(file, play)
            result += self.space_tasks(file, play)
        return result
