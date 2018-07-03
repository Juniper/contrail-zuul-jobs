from ansiblelint import AnsibleLintRule


class YAMLFileExtension(AnsibleLintRule):
    id = 'ANSIBLE-J0002'
    shortdesc = 'YAML files should have the .yaml file extension.'
    description = ''
    tags = ['formatting']
    done = []  # already noticed path list

    def match(self, file, text):
        path = file['path']
        if not path.endswith('.yaml') and path not in self.done:
            self.done.append(path)
            return True
        return False
