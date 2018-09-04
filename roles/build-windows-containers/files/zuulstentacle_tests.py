#!/usr/bin/env python3

import zuulstentacle
import os
import shutil
import unittest
import urllib.request

class ZuulJenkinsConnectorTests(unittest.TestCase):
    def setUp(self):
        self.configuration = ZuulJenkinsConnectorTests.TestConfiguration()
        self.zuul_jenkins_connector = zuulstentacle.CreateZuulJenkinsConnector(
            self.configuration)
        self.directory_prefix = "src"
        self.initial_working_directory = os.getcwd()
        self.setup_directory_structure()

    def setup_directory_structure(self):
        shutil.rmtree(self.directory_prefix, ignore_errors=True)
        os.mkdir(self.directory_prefix)
        os.mkdir(os.path.join(self.directory_prefix,
            self.configuration.gerrit_server))

    def tearDown(self):
        os.chdir(self.initial_working_directory)
        shutil.rmtree(self.directory_prefix, ignore_errors=True)

    def test_connector_returns_true_when_jenkins_job_succeeds(self):
        self.check_that_connector_returns_response_from_jenkins(True)

    def test_connector_returns_false_when_jenkins_job_fails(self):
        self.check_that_connector_returns_response_from_jenkins(False)

    def test_an_archive_is_available_when_jenkins_job_is_started(self):
        self.archive_is_available = False
        self.zuul_jenkins_connector.start_jenkins_job_and_wait_for_result =\
            self.check_if_an_archive_is_available_through_http
        self.zuul_jenkins_connector.handle_zuul_job()
        self.assertEqual(self.archive_is_available, True)

    def check_that_connector_returns_response_from_jenkins(self,
            response_from_jenkins):
        self.zuul_jenkins_connector.jenkins_manager =\
            ZuulJenkinsConnectorTests.TestJenkinsManager(response_from_jenkins)
        job_was_successful = self.zuul_jenkins_connector.handle_zuul_job()
        self.assertEqual(job_was_successful, response_from_jenkins)

    def check_if_an_archive_is_available_through_http(self):
        url = self.zuul_jenkins_connector.repository_provider.get_provider_url()
        with urllib.request.urlopen(url, None, 5) as response:
            if response.status == 200:
                self.archive_is_available = True
        return True

    class TestConfiguration:
        def __init__(self):
            self.archive_base_name = "repo"
            self.http_server_ip = "127.0.0.1"
            self.http_server_port = 0
            self.jenkins_address = "does.not.exist"
            self.jenkins_user = "jenkins.user"
            self.jenkins_password = "jenkins.password"
            self.jenkins_job = "jenkins.job"
            self.gerrit_server = "gerrit.server"

    class TestJenkinsManager:
        def __init__(self, result):
            self.result = result

        def authenticate_to_jenkins_server(self):
            pass

        def start_jenkins_job_and_wait_for_result(
                self, job_name, job_parameters):
            return self.result

if __name__ == "__main__":
    unittest.main()
