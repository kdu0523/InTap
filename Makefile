PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test demo

test:
	$(PYTHON) -m unittest discover -s tests -v

demo:
	$(PYTHON) -m intap profile --output .intap/profile.json
	$(PYTHON) -m intap prepare --profile .intap/profile.json --task examples/task.json --output .intap/run.json
