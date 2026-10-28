.PHONY: check verify-nami verify-mstest verify-submission
check:
	uv run --project packages/mstest-extensions --frozen python -B scripts/verify_marketplace.py
	cd packages/ancplua-dotnet && scripts/verify.sh
	cd packages/nami && uv run --frozen python -B scripts/validate.py
	cd packages/nami && uv run --frozen python -B -m unittest discover -s tests -v
	cd packages/nami && uv run --frozen python -B -m unittest discover -s plugins/nami/skills/csharp-union-types/scripts/tests -v
	cd packages/mstest-extensions && python3 -B scripts/test_inspect.py
	cd packages/mstest-extensions && python3 -B scripts/test_install.py
	$(MAKE) -C packages/mstest-extensions check
verify-nami:
	$(MAKE) -C packages/nami verify
verify-mstest:
	$(MAKE) -C packages/mstest-extensions verify-assertions
	cd packages/mstest-extensions && python3 -B scripts/verify_versions.py 4.5.1
	cd packages/mstest-extensions && python3 -B skills/mstest/scripts/verify_capabilities.py --mstest-sdk 4.5.1 --dotnet-sdk "$$(dotnet --version)" --hosting --native-aot

verify-submission:
	cd packages/prepare-plugin-submission && python3 -B -m unittest discover -s tests -v
	cd packages/prepare-plugin-submission && python3 -B -m unittest discover -s evals/runtime -v

.PHONY: check-docs
check-docs:
	npm run check:docs

.PHONY: check-skills
check-skills:
	python3 -B scripts/check_skills.py
