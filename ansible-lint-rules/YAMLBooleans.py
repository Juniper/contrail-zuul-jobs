from ansiblelint import AnsibleLintRule
import re

class YAMLBooleans(AnsibleLintRule):
    id = 'ANSIBLE-J0007'
    shortdesc = 'Booleans should be defined with true/false (lower case) values.'
    description = 'Booleans should be defined with true/false (lower case) values.'
    tags = ['formatting']
    done = []  # already noticed path list

    literal_bool = re.compile(': ?([Yy]es$|[Nn]o$|True|False)')

    def match(self, file, line):
        return self.literal_bool.search(line)
