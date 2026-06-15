# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Description: UT coverage for discovery search repository and service queries.
# Related requirements: W28A-274-I deliverables 1, 3, 4
# Tests: SI-02, SI-03
# Related tests: UT1.10

from __future__ import annotations

from types import SimpleNamespace

from src.core.search import DiscoveryDocument, DiscoverySearchService
from src.core.search.models import EntityIndexStatus, ProfileIndexStatus
import pytest


class _FakeJob:
    def __init__(self, status: str) -> None:
        self.status = SimpleNamespace(value=status)


class _FakeJobQueue:
    @staticmethod
    def get(job_id: str):
        return _FakeJob("succeeded")


class _FakeBackend:
    @staticmethod
    def get_queue_status():
        return {"succeeded": 1}


def _build_runtime(tmp_path):
    return SimpleNamespace(
        config={
            "search.discovery_index_path": str(tmp_path / "search.db"),
            "search.metadata_limit": 20,
            "search.content_limit": 20,
            "search.freshness_seconds": 3600,
        },
        job_queue=_FakeJobQueue(),
        job_backend=_FakeBackend(),
        access_control=SimpleNamespace(list_profiles=lambda: []),
    )
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_v1_10_1_repository_search_and_explain_match(tmp_path) -> None:
    service = DiscoverySearchService(_build_runtime(tmp_path))
    repository = service.repository

    repository.replace_profile_documents(
        "profile-1",
        [
            DiscoveryDocument(
                document_id="field:profile-1:sales:customers:email",
                profile_id="profile-1",
                namespace="sales",
                entity="customers",
                doc_kind="field",
                title="customers.email",
                keywords="customers customer email",
                body="Field email on customers in sales.",
                excerpt="Field email on customers in sales.",
                match_fields=["field", "types"],
                payload={"field_name": "email"},
            ),
            DiscoveryDocument(
                document_id="content:profile-1:sales:customers:C001",
                profile_id="profile-1",
                namespace="sales",
                entity="customers",
                doc_kind="content_excerpt",
                title="customers excerpt C001",
                keywords="customers customer email name",
                body="name: Acme | email: acme@example.com",
                excerpt="name: Acme | email: acme@example.com",
                match_fields=["name", "email"],
                payload={"record_id": "C001"},
            ),
        ],
        profile_status=ProfileIndexStatus(
            profile_id="profile-1",
            last_job_id="job-1",
            last_job_status="succeeded",
            last_synced_at="2026-03-24T00:00:00+00:00",
            freshness_state="fresh",
            namespace_count=1,
            entity_count=1,
            field_count=1,
            content_count=1,
            document_count=2,
        ),
        entity_statuses=[
            EntityIndexStatus(
                profile_id="profile-1",
                namespace="sales",
                entity="customers",
                last_job_id="job-1",
                last_job_status="succeeded",
                last_synced_at="2026-03-24T00:00:00+00:00",
                document_count=2,
                field_count=1,
                content_count=1,
            )
        ],
    )

    metadata_results = service.search_metadata(profile_id="profile-1", query="customer email")
    assert metadata_results
    assert metadata_results[0]["doc_kind"] == "field"
    assert metadata_results[0]["title"] == "customers.email"

    content_results = service.search_content(profile_id="profile-1", query="acme@example.com")
    assert content_results
    assert content_results[0]["doc_kind"] == "content_excerpt"

    explanation = service.explain_match(
        profile_id="profile-1",
        query="customer email",
        document_id="field:profile-1:sales:customers:email",
    )
    assert any(item["field"] == "title" for item in explanation["matched_components"])
    assert any(item["field"] == "keywords" for item in explanation["matched_components"])
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_v1_10_2_index_status_includes_queue_and_entity_status(tmp_path) -> None:
    service = DiscoverySearchService(_build_runtime(tmp_path))
    repository = service.repository
    repository.update_profile_status(
        ProfileIndexStatus(
            profile_id="profile-1",
            last_job_id="job-1",
            last_job_status="succeeded",
            last_synced_at="2026-03-24T00:00:00+00:00",
            freshness_state="fresh",
            namespace_count=1,
            entity_count=1,
            field_count=1,
            content_count=1,
            document_count=2,
        )
    )
    repository.update_entity_status(
        EntityIndexStatus(
            profile_id="profile-1",
            namespace="sales",
            entity="customers",
            last_job_id="job-1",
            last_job_status="succeeded",
            last_synced_at="2026-03-24T00:00:00+00:00",
            document_count=2,
            field_count=1,
            content_count=1,
        )
    )

    status = service.index_status(profile_ids=["profile-1"])
    assert status["items"][0]["profile_id"] == "profile-1"
    assert status["items"][0]["queue_status"] == {"succeeded": 1}
    assert status["items"][0]["entities"][0]["entity"] == "customers"
