GODEP_PATH=$(shell pwd)/Godeps/_workspace
ORIGINAL_PATH=$(shell echo $(GOPATH))
COMBINED_GOPATH=$(GODEP_PATH):$(ORIGINAL_PATH)

build:
	GOPATH=$(COMBINED_GOPATH) go build .
