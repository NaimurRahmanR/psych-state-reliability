.PHONY: test verify analyze audit publication robustness figures paper clean all-offline

test:
	python release_tools/run_frozen_tests.py

verify:
	python release_tools/verify_public_release.py

analyze:
	python release_tools/analyze_pilot20.py

audit:
	python release_tools/verify_human_audit.py

publication:
	python release_tools/make_publication_tables.py

robustness:
	python release_tools/robustness_audit.py

figures:
	python release_tools/make_pilot20_figures.py

paper:
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex && bibtex main && pdflatex -interaction=nonstopmode -halt-on-error main.tex && pdflatex -interaction=nonstopmode -halt-on-error main.tex

all-offline: test verify analyze audit publication robustness

clean:
	rm -f paper/*.aux paper/*.log paper/*.out paper/*.fls paper/*.fdb_latexmk paper/*.toc paper/*.blg paper/*.bbl
