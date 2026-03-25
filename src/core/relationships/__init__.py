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
# Description: Relationship service exports.
# Related requirements: RL-01, RL-02, RL-03
# Related tests: UT1.8, IT1.5

"""Relationship exports."""

from src.core.relationships.models import RelationshipRecord
from src.core.relationships.service import RelationshipService

__all__ = ["RelationshipRecord", "RelationshipService"]
