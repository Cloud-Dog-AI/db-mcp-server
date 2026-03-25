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
# Description: Elasticsearch seed module for the canonical connector test dataset.
# Related requirements: W28A-274-K deliverables 4, 8

"""Elasticsearch seed utilities for the canonical connector dataset."""

from __future__ import annotations

import os

from tests.fixtures.opensearch_seed import seed_opensearch, teardown_opensearch

DEFAULT_ELASTICSEARCH_URL = os.getenv("DB_MCP_TEST_ELASTICSEARCH_URL", "http://127.0.0.1:9201")


def seed_elasticsearch(*, base_url: str = DEFAULT_ELASTICSEARCH_URL) -> list[str]:
    """Seed the canonical dataset into Elasticsearch."""
    return seed_opensearch(base_url=base_url)


def teardown_elasticsearch(*, base_url: str = DEFAULT_ELASTICSEARCH_URL) -> None:
    """Drop seeded Elasticsearch indices."""
    teardown_opensearch(base_url=base_url)


if __name__ == "__main__":
    created = seed_elasticsearch()
    print("Elasticsearch seed completed for indices:", ", ".join(created))
