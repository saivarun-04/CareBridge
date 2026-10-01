# Makefile

.PHONY: install test lint demo

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

test:
	@echo "Running test suite..."
	pytest -q

lint:
	@echo "Running lint checks..."
	ruff check .

# Run the demo script (Stage 4)
# This runs the 3‑minute story in mock mode.
demo:
	@echo "Running CareBridge demo..."
	python scripts/demo.py
