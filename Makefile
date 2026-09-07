PYTHON ?= python3
HUGO ?= hugo

GENERATOR := scripts/generate_hall_pages.py

.PHONY: generate build serve ci

generate:
	$(PYTHON) $(GENERATOR)

build: generate
	$(HUGO) --minify

serve: generate
	$(HUGO) server

ci: build
	$(PYTHON) scripts/check_site.py public
