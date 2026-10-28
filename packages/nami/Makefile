SHELL := /bin/bash
.DEFAULT_GOAL := check
.NOTPARALLEL:
UNION_SOURCE ?=
UNION_CHECKOUT ?=
UNION := plugins/nami/skills/csharp-union-types
.PHONY: check test verify verify-fixtures verify-union check-union-sync sync-union

check:
	uv run --frozen python -B scripts/validate.py

test:
	uv run --frozen python -B -m unittest discover -s tests -v
	uv run --frozen python -B -m unittest discover -s $(UNION)/scripts/tests -v

verify: check test verify-fixtures verify-union

verify-fixtures:
	uv run --frozen python -B scripts/verify.py fixtures

verify-union:
	uv run --frozen python -B scripts/verify.py union

check-union-sync:
	@test -n "$(UNION_SOURCE)" || { echo "Set UNION_SOURCE to Nami's canonical csharp-union-types directory"; exit 2; }
	python3 -B "$(UNION_SOURCE)/scripts/sync.py" --target "$(CURDIR)/$(UNION)" $(if $(strip $(UNION_CHECKOUT)),--target "$(abspath $(UNION_CHECKOUT))")

sync-union:
	@test -n "$(UNION_SOURCE)" || { echo "Set UNION_SOURCE to Nami's canonical csharp-union-types directory"; exit 2; }
	python3 -B "$(UNION_SOURCE)/scripts/sync.py" --target "$(CURDIR)/$(UNION)" $(if $(strip $(UNION_CHECKOUT)),--target "$(abspath $(UNION_CHECKOUT))") --apply
