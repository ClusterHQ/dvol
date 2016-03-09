package cmd

import (
	"bytes"
	"io/ioutil"
	"testing"
)

func TestRmNoArgs(t *testing.T) {
	buf := bytes.NewBuffer([]byte{})
	cmd := NewCmdRm(buf)
	err := removeVolume(cmd, []string{}, buf)
	if err == nil {
		t.Error("Expected error result with no arguments")
	}
	expected := "Please specify a volume name."
	if err.Error() != expected {
		t.Errorf("Expected: %s Actual: %s", expected, err.Error())
	}
}

func TestRmInvalidVolumeName(t *testing.T) {
	buf := bytes.NewBuffer([]byte{})
	cmd := NewCmdRm(buf)
	err := removeVolume(cmd, []string{"foo/bar"}, buf)
	if err == nil {
		t.Error("Expected error result with invalid volume name")
	}
	expected := "Error: foo/bar is not a valid name"
	if err.Error() != expected {
		t.Errorf("Expected: %s Actual: %s", expected, err.Error())
	}
}

func TestRmVolumeDoesNotExist(t *testing.T) {
	// Setup
	originalBasepath := basePath
	dir, _ := ioutil.TempDir("", "test")
	basePath = dir

	// Test
	buf := bytes.NewBuffer([]byte{})
	cmd := NewCmdRm(buf)
	err := removeVolume(cmd, []string{"foo"}, buf)
	if err == nil {
		t.Error("Expected error result with non-existent volume")
	}

	expected := "Volume 'foo' does not exist, cannot remove it"
	if err.Error() != expected {
		t.Errorf("Expected: %s Actual: %s", expected, err.Error())
	}

	// Teardown
	basePath = originalBasepath
}
