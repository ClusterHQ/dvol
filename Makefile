PHONY: build test verify bootstrap go-bootstrap python-bootstrap

build:
	godep go build .

# 'test' will run the python tests using the dvol cli
test: build
	. venv/bin/activate \
	&& HYPOTHESIS_PROFILE=ci trial dvol_python.test_dvol \
	&& HYPOTHESIS_PROFILE=ci TEST_GOLANG_VERSION=1 DVOL_BINARY=$(PWD)/dvol trial dvol_python.test_dvol \
	&& scripts/verify-tests.sh

test-go: build
	. venv/bin/activate \
	&& HYPOTHESIS_PROFILE=dev TEST_GOLANG_VERSION=1 DVOL_BINARY=$(PWD)/dvol trial dvol_python.test_dvol \
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

memorydiskserver-docker-image:
	scripts/build-golang-docker-image.sh \
		--project "memorydiskserver" \
		--source-files "cmd/memorydiskserver/memorydiskserver.go" \
		--binaries "memorydiskserver" \
		--tag "latest"

dvol-golang-docker-image:
	scripts/build-golang-docker-image.sh \
		--project "dvol" \
		--source-files "dvol.go cmd/dvol-docker-plugin/dvol-docker-plugin.go" \
		--binaries "dvol dvol-docker-plugin bin/cp" \
		--tag "golang"

dvol-python-docker-image:
	# XXX depends on the network. but we're going to throw away the Python
	# version so maybe not so important?
	docker build -t clusterhq/dvol:latest .

# The following two targets install dvol and dvol-docker-plugin wrapper scripts
# globally (in /usr/local/bin) on the system, which is OK because Travis-CI
# gives us a whole new VM for each build.

test-dvol-python-acceptance: dvol-python-docker-image memorydiskserver-docker-image
	./install.sh # will reuse built clusterhq/dvol:latest
	. venv/bin/activate \
	&& trial dvol_python.test_plugin

test-dvol-golang-acceptance: dvol-golang-docker-image
	./install.sh golang # will reuse built clusterhq/dvol:golang
	. venv/bin/activate \
	&& TEST_GOLANG_VERSION=1 trial dvol_python.test_plugin.VoluminousTests.test_roundtrip_dvol_metadata_to_itself
