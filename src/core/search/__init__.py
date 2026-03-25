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
# Description: Public exports for db-mcp-server discovery search services.
# Related requirements: W28A-274-I deliverables 1, 2, 3, 4
# Related tests: UT1.9, UT1.10, ST1.7, IT1.6

"""Discovery search exports."""

from src.core.search.indexer import DiscoveryIndexer, build_fts5_query, normalise_search_terms
from src.core.search.models import DiscoveryDocument, EntityIndexStatus, ProfileIndexStatus
from src.core.search.repository import DiscoveryIndexRepository
from src.core.search.service import DiscoverySearchService

__all__ = [
    "DiscoveryDocument",
    "DiscoveryIndexRepository",
    "DiscoveryIndexer",
    "DiscoverySearchService",
    "EntityIndexStatus",
    "ProfileIndexStatus",
    "build_fts5_query",
    "normalise_search_terms",
]
