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
# Description: Backwards-compatible Mongo seed module shim.
# Related requirements: W28A-274-K deliverable 2
# Related tests: ST1.4, ST1.5, ST1.6, IT1.3, IT1.4, IT1.5

"""Backwards-compatible import surface for MongoDB seed helpers."""

from tests.fixtures.mongodb_seed import SEED_COLLECTIONS, clone_seed_collections, seed_mongodb, teardown_mongodb

__all__ = [
    "SEED_COLLECTIONS",
    "clone_seed_collections",
    "seed_mongodb",
    "teardown_mongodb",
]
