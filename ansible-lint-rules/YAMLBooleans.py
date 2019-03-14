from ansiblelint import AnsibleLintRule
import re

class YAMLBooleans(AnsibleLintRule):
    id = 'ANSIBLE-J0007'
    shortdesc = 'Booleans should be defined with true/false (lower case) values.'
    description = 'Booleans should be defined with true/false (lower case) values.'
    tags = ['formatting']

    literal_bool = re.compile('[a-z]: ?([Yy]es$|[Nn]o$|True$|False$)')

    def match(self, file, line):
        return self.literal_bool.search(line)
        
