#!/usr/bin/python3

from ansible.module_utils.basic import AnsibleModule
from jira import JIRA

DOCUMENTATION = '''
---
module: library

short_description: Module for creating tickets in jira

version_added: "1.0"

description:
    - Search by summary format for issue related with build number and branch
    - Create ticket if not exists
options:
    username:
        description:
            - Login to jira
        required = True
    password:
        description:
            - API token to jira
        required = True
    build_number:
        description:
            - Build number; parameter: "{{ zuul.build }}"
        required = True
    branch:
        description:
            - Branch of target build; parameter: "{{ zuul.branch }}"
        required = True

    details:
        description:
            - Build details 
        required = False
roles:
    - set-zuul-log-path-fact
    - contrail-common-libs2
dependencies:
    packages:
        - jira >= 2.0 # full list of python dependencies in roles/library/files/requirements.txt
author:
- Oleksandr Zhyhalo (@szhyhalo)
'''

EXAMPLES = '''
#  Usage example
- name: Create jira issue
  library:
    username: "{{ jira.username }}"     # Jira username
    password: "{{ jira.token }}"        # Jira API TOKEN
    build: "{{ zuul.build }}"           # Zuul build number
    branch: "{{ zuul.branch }}"         # Zuul build target branch
    details: "{{ stdout_lines }}"       # Build details
  when: not {{ zuul_success }}| bool    # create ticket only if build failed
  no_log: true                          # no log for passwords or sensitive data
'''


def search_for_ticket(jira, branch, build):
    """
Function responsible for searching jira issues by summary
    :param jira: open connection to Jira: jira.JIRA
    :param branch: target build branch: str
    :param build: zuul build number: str
    :return: issue found: bool
    """
    issues = jira.search_issues('project = JD AND type=Incident and updated <= -21d')
    found = [issue for issue in issues if branch in issue.fields.summary and build in issue.fields.summary]
    if found:
        return True
    return False


def create_new_issue(jira, branch, build, details):
    """
    :param jira: open connection to Jira: jira.JIRA
    :param branch: target build branch: str
    :param build: zuul build number: str
    :param details: Build details: str
    :return: new issue link: str
    """
    issue_dict = {
        'project': {'id': '10004'},
        'summary': 'Nightly - {} - {} - failed!'.format(branch, build),
        'description': 'Build number {} on branch {} FAILED!\nLogs can be found here: {}'.format(build, branch,
                                                                                                 details),
        'issuetype': {'name': 'Incident'},
        "components": [{"name": 'Buildcop'}],
    }
    new_issue = jira.create_issue(fields=issue_dict)
    return new_issue.permalink()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(required=True),
            password=dict(required=True),
            build_number=dict(required=True),
            branch=dict(required=True),
            details=dict(),
        )
    )
    result = dict(
        changed=False,
        original_message='',
        message=[]
    )
    username = module.params['username']
    token = module.params['password']
    build_number = module.params['build']
    branch = module.params['branch']
    try:
        details = module.params['details']
    except TypeError:
        details = "Link not delivered by Zuul"

    options = {
        'server': 'https://contrail-jws.atlassian.net'}
    jira = JIRA(options, basic_auth=(username, token))
    issue = search_for_ticket(jira, branch, build_number)
    if issue:
        result['message'] = ["Issue already in Jira"]
    else:
        result['message'].append(create_new_issue(jira, branch, build_number, details))
        result['changed'] = True
    module.exit_json(**result)


if __name__ == '__main__':
    main()
