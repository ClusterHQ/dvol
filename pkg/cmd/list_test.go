package cmd

import (
	"bytes"
	"io/ioutil"
	"testing"
)

func TestListNoArgs(t *testing.T) {
	// Setup
	originalBasePath := basePath
	dir, _ := ioutil.TempDir("", "test")
	basePath = dir

	// Test
	buf := bytes.NewBuffer([]byte{})
	cmd := NewCmdList(buf)
	err := listVolumes(cmd, []string{}, buf)
	if err != nil {
		t.Error("Unexpected error result with no arguments")
	}

	// Teardown
	basePath = originalBasePath
}

func TestListWrongNumberArgs(t *testing.T) {
	buf := bytes.NewBuffer([]byte{})
	cmd := NewCmdList(buf)
	err := listVolumes(cmd, []string{"invalid_arg"}, buf)
	if err == nil {
		t.Error("Expected error result with no arguments")
	}
	expected := "Wrong number of arguments."
	if err.Error() != expected {
		t.Errorf("Expected: %s Actual: %s", expected, err.Error())
	}
}
