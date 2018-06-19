from ansiblelint import AnsibleLintRule


class YAMLFileFormat(AnsibleLintRule):
    id = 'ANSIBLE-J0001'
    shortdesc = 'YAML files should begin with the YAML marker and end with a blank line.'
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
        last_char = ''

        try:
            first_line = _file.readline()
        except IndexError:  # there are empty files
            pass

        try:
            last_char = _file.readlines()[-1][-1]
        except IndexError:  # there are empty or one line files
            if first_line != '':
                last_char = first_line[-1]

        is_format_correct = first_line == '---\n' and last_char == '\n'
        if not is_format_correct and path not in self.done:
            self.done.append(path)
            return True
        return False
