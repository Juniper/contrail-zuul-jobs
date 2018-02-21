#!/usr/bin/env python

import contextlib
import json
import os
import subprocess
import sys

@contextlib.contextmanager
def chdir(path):
    curdir = os.getcwd()
    os.chdir(path)
    try: yield
    finally: os.chdir(curdir)

def parse_zuul_refs():
    """Returns a dictionary with projects and their refs.

    Zuulv3 passes all refs as GIT_REFS environment variable, in the following
    format: project^ref2,project^ref2.
    """
    projects = {}
    items = os.environ.get("GIT_REFS").split(",")
    for item in items:
        project, ref = item.split("^")
        if project not in projects:
            projects[project] = []
        projects[project].append(ref)
    return projects.items()

def get_path_for_project_name(project):
    """Returns a relative path for the given project."""
    mapping = {
        "contrail-controller": "controller",
        "contrail-vrouter": "vrouter",
        "contrail-sandesh": "tools/sandesh",
        "contrail-generateDS": "tools/generateds",
    }
    return mapping[project]

def get_changes_for_ref(project_path, ref):
    repo_path = os.path.join(contrail_sources, project_path)

    with chdir(repo_path):
        commit_id = subprocess.check_output(
            "git ls-remote gerrit | grep refs/changes/40/37240/1 | cut -f 1",
            shell=True
        ).strip()

        modified_files = subprocess.check_output(
            "git diff-tree --no-commit-id --name-only -r %s" % commit_id,
            shell=True
        ).strip()

    return modified_files.split("\n")

contrail_sources = os.path.join(                                                                                                                                                                                                                                       [30/1850]
    os.environ['WORKSPACE'],
    "contrail-" + os.environ['UPSTREAM_VERSION']
)

json_file = os.path.join(contrail_sources, "controller", "ci_unittests.json")
if not os.path.exists(json_file):
    sys.exit(0)

modified_dirs = set()
for project, refs in parse_zuul_refs():
    project_path = get_path_for_project_name(project)
    for ref in refs:
        files = get_changes_for_ref(project_path, ref)
        modified_dirs |= set([os.path.join(project_path, os.path.dirname(f)) for f in files])

    # special-case vrouter and generateDS projects
    if project in ["contrail-vrouter", "contrail-generateDS"] :
        modified_dirs.add(project_path)

with open(json_file, "r") as fh:
    test_filters = json.load(fh)

tests = []
for project, data in test_filters.items():
    skip = True
    for d in modified_dirs:
        if d in data["source_directories"]:
            skip = False
            break
    if skip:
        continue

    tests.extend(data["scons_test_targets"])
    # add transitive targets
    for m in data["misc_test_targets"]:
        tests.extend(test_filters[m]["scons_test_targest"])
print " ".join(tests)
