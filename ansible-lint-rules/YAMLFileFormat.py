from ansiblelint import AnsibleLintRule


class YAMLFileFormat(AnsibleLintRule):
    id = 'ANSIBLE-J0001'
    shortdesc = 'YAML files should begin with the YAML marker and end with a new line character.'
    description = 'YAML files should begin with the YAML marker `---` marking the start of the document' + \
                  'and end with a new line character.'
    tags = ['formatting']
    done = []  # already noticed path list

    def match(self, file, text):
        path = file['path']

        first_line = ''
        last_line = ''

        with open(path, 'r') as _file:
            try:
                first_line = _file.readline()
                last_line = _file.readlines()[-1]
            except IndexError:  # handle empty or one line files
                if first_line != '':
                    last_line = first_line[-1]

            is_format_correct = first_line == '---\n' and last_line == '\n'
            if not is_format_correct and path not in self.done:
                self.done.append(path)
                return True
        return False
