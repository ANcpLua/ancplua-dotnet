.PHONY: check test verify-assertions update-mstest-api check-mstest-api
check:
	python3 -B scripts/check_links.py
	python3 -B scripts/test_package.py

test:
	python3 -B scripts/test_inspect.py
	python3 -B scripts/test_install.py
	python3 -B scripts/test_package.py

verify-assertions:
	python3 -B skills/mstest-assertions/scripts/verify_examples.py

update-mstest-api:
	uv run --frozen python -B skills/mstest/scripts/generate_api.py

check-mstest-api:
	uv run --frozen python -B skills/mstest/scripts/generate_api.py --check
