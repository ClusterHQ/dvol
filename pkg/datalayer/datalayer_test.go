package datalayer

import (
	"io/ioutil"
	"testing"
)

func TestValidVolumeName(t *testing.T) {
	supposedBad := []string{"£", "-", "-a", "1", "",
		// 41 characters, more than 40
		"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
	supposedGood := []string{"a", "abc-123", "a12345", "abcde", "AbCdE"}
	for _, bad := range supposedBad {
		if ValidVolumeName(bad) {
			t.Error(bad + " is not a valid volume name, but it passed ValidVolumeName")
		}
	}
	for _, good := range supposedGood {
		if !ValidVolumeName(good) {
			t.Error(good + " is a valid volume name, but it failed ValidVolumeName")
		}
	}
}

func TestSwitchVolume(t *testing.T) {
	currentVolume := "foo"
	basePath, err := ioutil.TempDir("", "switch")
	if err != nil {
		t.Errorf("Could not create TempDir: %s\n", err)
	}
	err := SwitchVolume(basePath, currentVolume)
	if err != nil {
		t.Errorf("SwitchVolume failed: %s\n", err)
	}
	activeVolume, err := ActiveVolume()
	if err != nil {
		t.Error("Could not find ActiveVolume")
	}
	if activeVolume != "foo" {
		t.Errorf("%s is not equal to 'foo'", activeVolume)
	}
}
