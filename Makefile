
PHONY: build test verify bootstrap go-bootstrap python-bootstrap

build: 
	godep go build .

# 'test' will run the python tests using the cli
test: build
	source venv/bin/activate \
	HYPOTHESIS_PROFILE=ci trial dvol_python \
	&& HYPOTHESIS_PROFILE=ci DVOL_BINARY=$PWD/dvol trial -j2 dvol_python \
	&& scripts/verify-tests.sh 

# 'verify' ensures your golang code passes 'the basics'
# locally before committing e.g. gofmt, go vet etc
verify:
	scripts/verify-preflight.sh 
    
bootstrap: go-bootstrap python-bootstrap

# 'go-bootstrap' installs all of the golang tools required by dvol
# remember to add {GOPATH}/bin to your Path
go-bootstrap: godep cover vet goimports

godep:
	go get github.com/tools/godep

cover:
	go get golang.org/x/tools/cmd/cover

vet:
	go get golang.org/x/tools/cmd/vet

goimports:
	go get golang.org/x/tools/cmd/goimports

# 'python-bootstrap' installs all of python dependencies
# required by dvol.
python-bootstrap: venv
	source venv/bin/activate \
	&& pip install .

venv:
	test -d venv || virtualenv venv
