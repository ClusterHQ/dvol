
PHONY: test verify bootstrap go-bootstrap python-bootstrap

build: 
	godep go build .

# test will run the python tests using the cli 
test: build 
	trial -j2 dvol_python \
	&& HYPOTHESIS_PROFILE=ci trial dvol_python \
	&& HYPOTHESIS_PROFILE=ci  DVOL_BINARY=$PWD/dvol trial -j2 dvol_python \
	&& scripts/verify-tests.sh 

# verify ensures your golang code passes 'the basics' 
# locally before committing e.g. gofmt, go vet etc
verify:
	scripts/verify-preflight.sh 
    
bootstrap: go-bootstrap python-bootstrap

# go-bootstrap installs all of the golang tools required by dvol
# remember to add {GOPATH}/bin to your Path
go-bootstrap:  
	go get github.com/tools/godep \
	&& go get golang.org/x/tools/cmd/cover \
	&& go get golang.org/x/tools/cmd/vet \
	&& go get golang.org/x/tools/cmd/goimports

# python-bootstrap installs all of python dependancies
# required by dvol. It is recommended to use a virtualenv.
python-bootstrap:
	pip install --upgrade pip>=7 \
	&& pip install wheel \
	&& pip install .
