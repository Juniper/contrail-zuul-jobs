#!/usr/bin/python3

from ansible.module_utils.basic import AnsibleModule
from jira import JIRA

DOCUMENTATION = '''
---
module: jira-handler

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
    build:
        description:
            - Build number; parameter: "{{ zuul.build }}"
        required = True
    branch:
        description:
            - Branch of target build; parameter: "{{ zuul.branch }}"
        required = True

    details:
        description:
            - Link to log server
        required = False
        
dependencies:
    roles:
        - set-zuul-log-path-fact
    packages:
        - jira >= 2.0 # full list of python dependencies in roles/jira-handler/files/requirements.txt
author:
- Oleksandr Zhyhalo (@szhyhalo)
    
'''

EXAMPLES = '''
# simple usage
- name: Create jira issue
  jira-handler:
    username: "{{ username }}" # Jira username
    password: "{{ password }}" # Jira API TOKEN
    build: "{{ zuul.build }}" # Zuul build number
    branch: "{{ zuul.branch }}" # Zuul build target branch
    details: "{{ stdout_lines }}" # where log_url is defined according to your specifications 
  when: not {{ zuul_success }}| bool # create ticket only if build failed 
  no_log: true # no log for passwords or sensitive data 
'''


def search_for_ticket(jira, branch, build):
    """
Function responsible for searching jira issues by summary
    :param jira: open connection to Jira: jira.JIRA
    :param branch: target build branch: str
    :param build: zuul build number: str
    :return: issue found: bool
    """
    issues = jira.search_issues('type=Incident and project=JD and status != closed')
    found = [issue for issue in issues if branch in issue.fields.summary and build in issue.fields.summary]
    if found:
        return True
    return False


def create_new_issue(jira, branch, build, details):
    """
    :param jira: open connection to Jira: jira.JIRA
    :param branch: target build branch: str
    :param build: zuul build number: str
    :param details: zuul link to log: str
    :return: new issue link: str
    """
    issue_dict = {
        'project': {'id': '10004'},
        'summary': 'Nightly - {} - {} - FAILED!'.format(branch, build),
        'description': 'Build number {} on branch {} FAILED!\nLogs can be found here: {}'.format(build, branch,
                                                                                                 details),
        'issuetype': {'name': 'Incident'},
        "components": [{"name": 'Buildcop'}],
    }
    new_issue = jira.create_issue(fields=issue_dict)
    return new_issue.permalink()


def main():
    """
Main function
    """
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(required=True),
            password=dict(required=True),
            build=dict(required=True),
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
    api = module.params['password']
    build = module.params['build']
    branch = module.params['branch']
    try:
        details = module.params['details']
    except TypeError:
        details = "Link not deliver by Zuul"

    options = {
        'server': 'https://contrail-jws.atlassian.net'}
    jira = JIRA(options, basic_auth=(username, api))
    issue = search_for_ticket(jira, branch, build)
    if issue:
        result['message'] = ["Issue already in Jira"]
    else:
        result['message'].append(create_new_issue(jira, branch, build, details))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
