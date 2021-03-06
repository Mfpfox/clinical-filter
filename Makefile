#!/usr/bin/make -f

SHELL = /bin/bash

PREFIX                    := /software/ddd/internal/clinical-filter
GIT_URI                   := ssh://git.internal.sanger.ac.uk/repos/git/ddd/clinical-filter.git

TMPDIR                    := $(shell mktemp -d)
SRCDIR                    := $(TMPDIR)/clinical-filter-$(CLINICAL_FILTER_VERSION)

CLINICAL_FILTER_PREFIX    := $(PREFIX)/clinical-filter-$(CLINICAL_FILTER_VERSION)
CLINICAL_FILTER_CONFIGDIR := $(CLINICAL_FILTER_PREFIX)/config

INSTALL                   := /usr/bin/install
CHMOD                     := Du=rwx,Dg=rwx,Do=rx,Fu=rw,Fg=rw,Fo=r




usage:
	@echo "Usage: CLINICAL_FILTER_VERSION=XXX install" >&2

.PHONY: clinical-filter-version

clinical-filter-version:
	@if [ -n "${CLINICAL_FILTER_VERSION}" ]; then echo "Installing clinical-filter-${CLINICAL_FILTER_VERSION}"; else echo "Usage: CLINICAL_FILTER_VERSION=X.X.X install";exit 1; fi

install: clinical-filter-version $(SRCDIR)
	$(MAKE) -C $(SRCDIR) TMPDIR=$(TMPDIR) CLINICAL_FILTER_VERSION=$(CLINICAL_FILTER_VERSION) clean-srcdir-git install-python clean-tmpdir


$(SRCDIR): $(TMPDIR)/clinical-filter-$(CLINICAL_FILTER_VERSION).zip
	cd $(TMPDIR) && unzip $<

$(TMPDIR)/clinical-filter-$(CLINICAL_FILTER_VERSION).zip:
	git archive --format zip --output $(TMPDIR)/clinical-filter-$(CLINICAL_FILTER_VERSION).zip --remote $(GIT_URI) --prefix clinical-filter-$(CLINICAL_FILTER_VERSION)/ $(CLINICAL_FILTER_VERSION)

clean-srcdir-git:
	find $(SRCDIR) | grep "/\.gitignore"$ | xargs -I '{}' rm {}

install-python:
	python setup.py install --user ; rsync -rp --chmod=$(CHMOD) $(SRCDIR)/clinicalfilter/ $(CLINICAL_FILTER_PREFIX)

clean-tmpdir:
	rm -r $(TMPDIR)

test:
	python3 setup.py test
