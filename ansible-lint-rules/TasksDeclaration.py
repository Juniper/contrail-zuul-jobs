from ansiblelint import AnsibleLintRule


class TasksDeclaration(AnsibleLintRule):
    id = 'ANSIBLE-J0004'
    shortdesc = 'Tasks declaration should have a specific form.'
    description = 'N/A'
    tags = ['formatting']
    def check_tasks_name(self, file, play):
        declaration_errors = []
        task_name = play['name']
        if not task_name[0].islower():
            declaration_errors.append(({task_name: '...'},
                'Line: {} - Task name: [{}] - should start with lowercase!'.format(
                play['__line__'], task_name)))
        return declaration_errors
    def matchplay(self, file, play):
        result = []
        if file['type'] != 'playbook':
            return False
        if 'name' in play:
            result += self.check_tasks_name(file, play)
            return result
