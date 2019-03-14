from ansiblelint import AnsibleLintRule
import re

class YAMLBooleans(AnsibleLintRule):
    id = 'ANSIBLE-J0007'
    shortdesc = 'Booleans should be defined with True/False (or true/false) values.'
    description = 'Booleans should be defined with True/False (or true/false) values.'
    tags = ['formatting']
    done = []  # already noticed path list

    literal_bool = re.compile(': ?(0|1|Yes|yes|No|no)')

    def match(self, file, line):
        return self.literal_bool.search(line)
