"""Tests for the secured cron endpoint (POST /cron/)."""

import json

import pytest
from django.test import TestCase, Client, override_settings
from django.urls import reverse


@pytest.mark.integration
@override_settings(CRON_API_KEY="test-cron-secret-key")
class TestCronEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("cron-run-tasks")
        self.auth_header = "Bearer test-cron-secret-key"

    # --- Auth tests ---

    def test_missing_auth_header_returns_403(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"tasks": ["expire_trials"]}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_invalid_token_returns_403(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"tasks": ["expire_trials"]}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer wrong-key",
        )
        assert response.status_code == 403

    def test_non_bearer_auth_returns_403(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"tasks": ["expire_trials"]}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz",
        )
        assert response.status_code == 403

    @override_settings(CRON_API_KEY="")
    def test_unconfigured_key_returns_500(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"tasks": ["expire_trials"]}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer anything",
        )
        assert response.status_code == 500

    def test_get_method_not_allowed(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.auth_header)
        assert response.status_code == 405

    # --- Request validation ---

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            self.url,
            data="not json",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        assert response.status_code == 400

    def test_empty_tasks_list_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"tasks": []}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        assert response.status_code == 400

    def test_unknown_task_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"tasks": ["nonexistent_task"]}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        assert response.status_code == 400
        data = response.json()
        assert "nonexistent_task" in data["error"]
        assert "available" in data

    # --- Task execution ---

    def test_valid_task_runs_and_returns_200(self):
        """expire_trials with no matching data should return 0 and succeed."""
        response = self.client.post(
            self.url,
            data=json.dumps({"tasks": ["expire_trials"]}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "expire_trials" in data["results"]
        assert data["results"]["expire_trials"]["status"] == "ok"

    def test_multiple_tasks_run(self):
        """Multiple valid tasks run and each gets a result entry."""
        response = self.client.post(
            self.url,
            data=json.dumps({"tasks": ["expire_trials", "expire_grace_periods"]}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"]["expire_trials"]["status"] == "ok"
        assert data["results"]["expire_grace_periods"]["status"] == "ok"

    def test_all_tasks_runs_entire_registry(self):
        """{"tasks": ["all"]} runs all registered tasks."""
        response = self.client.post(
            self.url,
            data=json.dumps({"tasks": ["all"]}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        # Should have all 6 registered tasks
        assert len(data["results"]) == 6
        for task_result in data["results"].values():
            assert task_result["status"] == "ok"
            assert "elapsed_seconds" in task_result
