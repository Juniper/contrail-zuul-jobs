from ansiblelint import AnsibleLintRule


class YAMLFileFormat(AnsibleLintRule):
    id = 'ANSIBLE-J0001'
    shortdesc = 'YAML File Format'
    description = 'YAML files should begin with the YAML marker `---` marking the start of the document' + \
                  'and end with a blank line.'
    tags = ['formatting']
    done = []  # already noticed path list

    def match(self, file, text):
        if file['type'] != 'playbook':
            return False

        path = file['path']

        _file = open(path, 'r')

        first_line = ''
        last_line = ''

        try:
            first_line = _file.readline()
        except IndexError:  # there are empty or one line files
            pass

        try:
            last_line = _file.readlines()[-1]
        except IndexError:  # there are empty or one line files
            pass

        is_format_correct = first_line == '---\n' and last_line == '\n'
        if not is_format_correct and path not in self.done:
            self.done.append(path)
            return True
        return False
