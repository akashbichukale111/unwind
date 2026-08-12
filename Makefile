.DEFAULT_GOAL := help
SHELL := /bin/bash
PY := .venv/bin/python
PIP := uv pip install --python .venv/bin/python

FIRESTORE_EMULATOR_HOST ?= localhost:8080
export FIRESTORE_EMULATOR_HOST

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

.venv:
	uv venv --python 3.12 .venv

.PHONY: install
install: .venv ## Install runtime + dev dependencies into .venv
	$(PIP) -e ".[dev]"

.PHONY: emulator
emulator: ## Start the Firestore emulator in the foreground (needs Java 11+)
	./infra/emulator.sh

.PHONY: dev
dev: ## Run the API against the Firestore emulator + in-process Pub/Sub shim
	./infra/dev.sh

.PHONY: test
test: ## Run the test suite
	$(PY) -m pytest -q

.PHONY: lint
lint: ## Lint and format-check
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

.PHONY: corpus
corpus: ## Regenerate the committed corpus (output must be byte-identical)
	$(PY) -m corpus.generate --out corpus/data

.PHONY: corpus-verify
corpus-verify: ## Prove the generator is deterministic (regenerate + diff manifest)
	$(PY) -m corpus.generate --verify --out corpus/data

.PHONY: eval
eval: ## Run the eval harness over evals/scenarios (zero scenarios is a valid run)
	$(PY) -m evals.harness --scenarios evals/scenarios --out evals/results

.PHONY: smoke
smoke: ## Run the throwaway ADK smoke agent (requires Vertex credentials)
	$(PY) -m agents.smoke.run

.PHONY: web-ui
web-ui: ## Launch `adk web` for local tracing during development
	.venv/bin/adk web agents

# ---------------------------------------------------------------------------
# Task 1 has not built these. They fail loudly rather than printing a fake pass.
# ---------------------------------------------------------------------------
.PHONY: demo
demo: ## [NOT BUILT - Task 5] End-to-end cascade demo
	@echo "make demo: NOT BUILT."
	@echo "The end-to-end cascade demo is scheduled for Task 5."
	@echo "Task 1 delivers scaffolding + corpus only. Failing loudly on purpose."
	@exit 1

.PHONY: golden
golden: ## [NOT BUILT - Task 4] Golden-transcript regression run
	@echo "make golden: NOT BUILT."
	@echo "Golden transcripts require the cascade (Task 2) and the court (Task 4)."
	@echo "Task 1 delivers scaffolding + corpus only. Failing loudly on purpose."
	@exit 1
