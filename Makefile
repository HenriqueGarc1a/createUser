VERSION := $(shell cat VERSION)
IMAGE := ubuntu-user-manager-builder

.PHONY: build package clean release

build:
	docker build -t $(IMAGE):$(VERSION) -t $(IMAGE):latest .

package:
	mkdir -p dist
	docker run --rm -v "$(CURDIR)/dist:/dist" $(IMAGE):latest

clean:
	rm -rf dist build \
		packaging/pyinstaller/build packaging/pyinstaller/dist \
		$(shell find . -name __pycache__ -type d)

release: clean build package
