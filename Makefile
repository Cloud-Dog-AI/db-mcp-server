PYTHON ?= .venv/bin/python

.PHONY: runtime-preflight lint test-unit

runtime-preflight:
	$(PYTHON) -c 'from src.common.runtime_contract import enforce_runtime; enforce_runtime()'
	$(PYTHON) --version

lint: runtime-preflight
	# Preserve the inherited lint-debt baseline while enforcing syntax/name correctness.
	$(PYTHON) -m ruff check --ignore E401,E402,F401,F541,F841 src tests start_api_server.py start_web_server.py start_mcp_server.py start_a2a_server.py

test-unit: runtime-preflight
	$(PYTHON) -m pytest tests/unit --env tests/env-UT
