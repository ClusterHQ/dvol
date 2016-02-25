
PHONY: build test verify bootstrap go-bootstrap python-bootstrap

build:
	godep go build .

# 'test' will run the python tests using the dvol cli
test: build
	. venv/bin/activate \
	HYPOTHESIS_PROFILE=ci trial dvol_python \
	&& HYPOTHESIS_PROFILE=ci TEST_DVOL_BINARY=1 DVOL_BINARY=$(PWD)/dvol trial -j2 dvol_python \
	&& scripts/verify-tests.sh

# 'verify' ensures your golang code passes 'the basics'
# locally before committing e.g. gofmt, go vet etc
verify:
	scripts/verify-preflight.sh

# 'bootstrap' installs all of the python and golang prerequisites
bootstrap: go-bootstrap python-bootstrap

# 'go-bootstrap' installs all of the golang tools required by dvol
# remember to add {GOPATH}/bin to your Path
go-bootstrap: godep cover vet goimports gotestcover

godep:
	go get github.com/tools/godep

cover:
	go get golang.org/x/tools/cmd/cover

vet:
	go get golang.org/x/tools/cmd/vet

gotestcover:
	go get github.com/pierrre/gotestcover

goimports:
	go get golang.org/x/tools/cmd/goimports

# 'python-bootstrap' installs all of python dependencies
# required by dvol.
python-bootstrap: venv
	. venv/bin/activate \
	&& pip install .

venv:
	test -d venv || virtualenv venv
