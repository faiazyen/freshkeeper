PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help venv install data audit embeddings train fusion evaluate tflite \
        bench diagrams demo serve screenshots test coverage lint all clean

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

venv: ## create the virtual environment (needs Python 3.12)
	python3.12 -m venv .venv && $(PIP) install -U pip

install: ## install dependencies
	$(PIP) install -r requirements.txt

data: ## download and split the image corpus
	bash scripts/download_dataset.sh
	$(PY) scripts/prepare_dataset.py

audit: ## detect near-duplicate leakage and build the group-aware split
	$(PY) scripts/audit_dataset.py

embeddings: ## cache frozen-backbone embeddings
	$(PY) -m freshkeeper.ml.embeddings

train: ## train the visual CNN (two-stage transfer learning)
	$(PY) -m freshkeeper.ml.train_cnn

corpus: ## generate the paired sensor corpus
	$(PY) -m freshkeeper.ml.sensor_corpus

fusion: ## train the fusion model and the ablation baselines
	$(PY) -m freshkeeper.ml.train_fusion

evaluate: ## evaluate on the test split and plot the results
	$(PY) -m freshkeeper.ml.evaluate

tflite: ## export to TensorFlow Lite and benchmark the variants
	$(PY) -m freshkeeper.ml.export_tflite

bench: ## measure end-to-end per-item inference cost
	$(PY) scripts/benchmark_pipeline.py

diagrams: ## regenerate the schematic and analysis figures
	$(PY) scripts/make_diagrams.py

demo: ## seed the demo database with an accelerated simulation
	$(PY) scripts/seed_demo.py

serve: ## run the web interface against the demo database
	# Fixed token so the screenshot script can log in. Omit --token in
	# real use and the server generates one and prints it.
	$(PY) scripts/run_server.py --db data/demo.db --port 5055 --token devtoken

screenshots: ## capture interface figures (server must be running)
	$(PY) scripts/capture_screenshots.py

test: ## run the test suite
	$(PY) -m pytest tests/ -q

coverage: ## run the tests with a coverage report
	$(PY) -m pytest tests/ -q --cov=freshkeeper --cov-report=term-missing

all: data audit embeddings train corpus fusion evaluate tflite bench diagrams demo ## full pipeline

clean: ## remove generated artefacts, keeping the raw download
	rm -rf data/processed data/embeddings data/sensor_corpus data/*.db* \
	       models/*.keras models/tflite models/*.npy results docs/figures
