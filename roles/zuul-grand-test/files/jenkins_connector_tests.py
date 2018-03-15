#!/usr/bin/env python3

import jenkins_connector
import unittest

class ZuulsTentacleTests(unittest.TestCase):
    def setUp(self):
        self.configuration = ZuulsTentacleTests.TestConfiguration()
        self.zuuls_tentacle = jenkins_connector.CreateZuulsTentacle(
            self.configuration)

    class TestConfiguration:
        def __init__(self):
            self.archive_base_name = "repo"
            self.http_server_ip = "127.0.0.1"
            self.http_server_port = 0
            self.jenkins_address = "does.not.exist"
            self.jenkins_user = "jenkins.user"
            self.jenkins_password = "jenkins.password"
            self.jenkins_job = "jenkins.job"
            self.gerrit_server = ".."

    def test_zuuls_tentacle_returns_true_when_jenkins_job_succeeds(self):
        self.zuuls_tentacle.start_jenkins_job_and_wait_for_result =\
            self.return_success
        job_was_successful = self.zuuls_tentacle.handle_zuul_job()
        self.assertEqual(job_was_successful, True)

    def test_zuuls_tentacle_returns_false_when_jenkins_job_fails(self):
        self.zuuls_tentacle.start_jenkins_job_and_wait_for_result =\
            self.return_failure
        job_was_successful = self.zuuls_tentacle.handle_zuul_job()
        self.assertEqual(job_was_successful, False)

    def test_an_archive_is_available_when_jenkins_job_is_started(self):
        self.archive_is_available = False
        self.zuuls_tentacle.start_jenkins_job_and_wait_for_result =\
            self.check_if_an_archive_is_available_through_http
        self.zuuls_tentacle.handle_zuul_job()
        self.assertEqual(self.archive_is_available, True)

    def return_success(self):
        return True

    def return_failure(self):
        return False

    def check_if_an_archive_is_available_through_http(self):
        self.archive_is_available = True
        # TODO do actual test
        return True

if __name__ == "__main__":
    unittest.main()
