GODEP_PATH=$(shell pwd)/Godeps/_workspace
ORIGINAL_PATH=$(shell echo $(GOPATH))
COMBINED_GOPATH=$(GODEP_PATH):$(ORIGINAL_PATH)

PHONY: test go-hack go-bootstrap

build: 
	GOPATH=$(COMBINED_GOPATH) go build .

# test will run the python tests using the cli 
test: build 
	trial -j2 dvol_python \
  	&& TEST_DVOL_BINARY=1 DVOL_BINARY=$PWD/dvol trial -j2 dvol_python \

# go-hack ensures your code passes 'the basics' 
# locally before committing e.g. gofmt, go vet etc
go-hack:
	scripts/run-preflight.sh

# go-bootstrap installs all of the golang tools required by dvol
# remember to add {GOPATH}/bin to your Path
go-bootstrap:  
	go get github.com/tools/godep \
	&& go get golang.org/x/tools/cmd/cover \
	&& go get golang.org/x/tools/cmd/vet \
	&& go get golang.org/x/tools/cmd/goimports
