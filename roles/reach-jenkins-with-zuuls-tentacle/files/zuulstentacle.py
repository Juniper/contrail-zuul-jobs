#!/usr/bin/env python3

import argparse
import http.server
import jenkinsapi
import jenkinsapi.jenkins
import os
import shutil
import sys
import threading
import urllib.error
import urllib.request
import urllib.response
import re

tool_description =\
        "Zuul's Tentacle - simple tool for integrating Zuul v3 with Jenkins"

class ZuulJenkinsConnector:
    def __init__(self, repository_provider, jenkins_manager, jenkins_job, build_parameters):
        self.repository_provider = repository_provider
        self.jenkins_manager = jenkins_manager
        self.jenkins_job = jenkins_job
        self.build_parameters = build_parameters

    def handle_zuul_job(self):
        self.repository_provider.start_server_with_repositories()
        self.repositories_archive_name =\
            self.repository_provider.prepare_archive_with_repositories()
        self.setup_repositories_archive_url()
        job_was_successful = self.start_jenkins_job_and_wait_for_result()
        self.repository_provider.shutdown_server_with_repositories()
        return job_was_successful

    def setup_repositories_archive_url(self):
        self.repositories_archive_url = (
            self.repository_provider.get_provider_url()
            + "/"
            + self.repositories_archive_name)

    def start_jenkins_job_and_wait_for_result(self):
        self.jenkins_manager.authenticate_to_jenkins_server()
        print(("Starting Jenkins job\n" +
            "    job name: \"{}\"\n" +
            "Docker registry IP: {}\n" .format(self.build_parameters["DOCKER_REGISTRY"]) +
            "    URL to repository contents: {}.").format(
                self.jenkins_job, self.repositories_archive_url))
        self.build_parameters["REPOSITORIES_ARCHIVE_URL"] = self.repositories_archive_url

        print("Jenkins_job {}" .format(self.jenkins_job))
        print("Build parameters: {}".format(self.build_parameters))
        job_was_successful =\
            self.jenkins_manager.start_jenkins_job_and_wait_for_result(
                self.jenkins_job, self.build_parameters)
        return job_was_successful

class RepositoryProvider:
    def __init__(self, archive_base_name, http_server_ip, http_server_port,floating_ip,directory):
        self.archive_base_name = archive_base_name
        self.http_server_ip = http_server_ip
        self.http_server_port = 32234
        self.floating_ip = floating_ip
        self.archive_format = "zip"
        self.http_server = None
        self.http_server_thread = None
        self.directory = directory

    def start_server_with_repositories(self):
        server_address = (self.http_server_ip, self.http_server_port)
        self.http_server = http.server.HTTPServer(
            server_address, http.server.SimpleHTTPRequestHandler)
        self.http_server_thread = threading.Thread(
            None,
            http.server.HTTPServer.serve_forever,
            "HTTP server thread",
            (self.http_server,))
        self.http_server_thread.start()
        print("Floating IP: {}" .format(self.floating_ip))
        print("Directory to archive {}" .format(self.directory))
        print("Repository provider: HTTP server address: {}".format(
            self.get_provider_url()))

    def prepare_archive_with_repositories(self):
        available_archive_format_names =\
            [i[0] for i in shutil.get_archive_formats()]
        if not self.archive_format in available_archive_format_names:
            raise Exception("Archive format {} is not supported.".format(
                self.archive_format))
        shutil.make_archive(self.archive_base_name, self.archive_format, self.directory)
        return "{}.{}".format(self.archive_base_name, self.archive_format)

    def get_provider_url(self):
        address = self.http_server.server_address
        return "http://{}:{}".format(self.floating_ip, address[1])

    def shutdown_server_with_repositories(self):
        self.http_server.shutdown()
        self.http_server_thread.join()

class JenkinsManager:
    def __init__(self, jenkins_address, jenkins_user, jenkins_password):
        self.jenkins_address = jenkins_address
        self.jenkins_user = jenkins_user
        self.jenkins_password = jenkins_password

    def authenticate_to_jenkins_server(self):
        self.jenkins = jenkinsapi.jenkins.Jenkins(
            self.jenkins_address, self.jenkins_user, self.jenkins_password)

    def start_jenkins_job_and_wait_for_result(self, job_name, job_parameters):
        job = self.jenkins[job_name]
        qi = job.invoke(build_params=job_parameters, block=True)
        print("QI: {}" .format(qi))
        build = qi.get_build()
        job_status = build.get_status()
        print("Jenkins job finished with status: {}".format(job_status))
        last_build = job.get_last_buildnumber()
        full_job_name = job.get_full_name()
        names = re.split('/', full_job_name)
        print("Job log {}/job/{}/job/{}/{}/".format(self.jenkins_address, names[0], names[1], last_build))
        job_was_successful = (job_status == jenkinsapi.constants.STATUS_SUCCESS)
        return job_was_successful

class ConfigurationManager:
    def __init__(self):
        self.argument_parser = None

    def fetch_configuration(self):
        self.create_argument_parser()
        self.setup_argument_parser()
        arguments = self.argument_parser.parse_args()
        arguments.archive_base_name = "repos"
        return arguments

    def create_argument_parser(self):
        self.argument_parser = argparse.ArgumentParser(
            description=tool_description)

    def setup_argument_parser(self):
        self.argument_parser.add_argument(
            "--jenkins_address",
            dest="jenkins_address",
            help="IP address of Jenkins server",
            required=True)
        self.argument_parser.add_argument(
            "--jenkins_job",
            dest="jenkins_job",
            help="Name of Jenkins job that should be invoked",
            required=True)
        self.argument_parser.add_argument(
            "--jenkins_user",
            dest="jenkins_user",
            default="Administrator",
            help="Jenkins user")
        self.argument_parser.add_argument(
            "--jenkins_password",
            dest="jenkins_password",
            default="hunter2",
            help="Password of Jenkins user")
        self.argument_parser.add_argument(
            "--http_server_ip",
            dest="http_server_ip",
            help="IP of HTTP server providing repositories",
            required=True)
        self.argument_parser.add_argument(
            "--floating_ip",
            dest="floating_ip",
            help="Floating IP server providing repositories",
            required=True)
        self.argument_parser.add_argument(
            "--http_server_port",
            dest="http_server_port",
            default=0,
            help="Port of HTTP server providing repositories")
        self.argument_parser.add_argument(
            "--docker_registry",
            dest="docker_registry",
            default=0,
            help="Docker registry address")
        self.argument_parser.add_argument(
            "--directory",
            dest="directory",
            default=0,
            help="Directory to archive")
        self.argument_parser.add_argument(
            "--docker_build_number",
            dest="docker_build_number",
            default=0,
            help="Build number")
        self.argument_parser.add_argument(
            "--docker_container_tag",
            dest="docker_container_tag",
            help="Container tag")
        self.argument_parser.add_argument(
            "--windows_version",
            dest="windows_version",
            help="Windows Server version")
        self.argument_parser.add_argument(
            "--zuul_build_id",
            dest="zuul_build_id",
            default=0,
            help="Unique zuul build number")
        self.argument_parser.add_argument(
            "--zuul_log_path",
            dest="zuul_log_path",
            default=0,
            help="Log path for tentacle logs")
        self.argument_parser.add_argument(
            "--branch",
            dest="branch",
            help="Branch")
        self.argument_parser.add_argument(
            "--test_level",
            dest="test_level",
            help="Sets TEST_LEVEL passed to Jenkins job. Available options are 'None', 'Sanity' and 'All'")

def GetBuildParameters(configuration):
    build_parameters = {
        "DOCKER_REGISTRY": configuration.docker_registry,
        "DOCKER_BUILD_NUMBER": configuration.docker_build_number,
        "ZUUL_UUID": configuration.zuul_build_id,
        "ZUUL_LOG_PATH": configuration.zuul_log_path,
        "ZUUL_BRANCH": configuration.branch,
    }
    if configuration.test_level:
        build_parameters["TEST_LEVEL"] = configuration.test_level
    if configuration.docker_container_tag:
        build_parameters["DOCKER_CONTAINER_TAG"] = configuration.docker_container_tag
    if configuration.windows_version:
        build_parameters["WINDOWS_VERSION"] = configuration.windows_version

    return build_parameters

def CreateZuulJenkinsConnector(configuration):
    repository_provider = RepositoryProvider(
        configuration.archive_base_name,
        configuration.http_server_ip,
        configuration.http_server_port,
        configuration.floating_ip,
        configuration.directory)
    jenkins_manager = JenkinsManager(
        configuration.jenkins_address,
        configuration.jenkins_user,
        configuration.jenkins_password)
    zuuls_tentacle = ZuulJenkinsConnector(
        repository_provider,
        jenkins_manager,
        configuration.jenkins_job,
        GetBuildParameters(configuration))
    return zuuls_tentacle

def ReachJenkinsByZuulsTentacle(configuration):
    zuuls_tentacle = CreateZuulJenkinsConnector(configuration)
    job_was_successful = zuuls_tentacle.handle_zuul_job()
    return job_was_successful

if __name__ == "__main__":
    configuration_manager = ConfigurationManager()
    configuration = configuration_manager.fetch_configuration()
    job_was_successful = ReachJenkinsByZuulsTentacle(configuration)
    sys.exit(not job_was_successful)
