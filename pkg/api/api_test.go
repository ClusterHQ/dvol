package api

import (
	"io/ioutil"
	"testing"
)

func TestValidName(t *testing.T) {
	supposedBad := []string{"£", "-", "-a", "1", "",
		// 41 characters, more than 40
		"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
	supposedGood := []string{"a", "abc-123", "a12345", "abcde", "AbCdE"}
	for _, bad := range supposedBad {
		if ValidName(bad) {
			t.Error(bad + " is not a valid volume/variant name, but it passed ValidName")
		}
	}
	for _, good := range supposedGood {
		if !ValidName(good) {
			t.Error(good + " is a valid volume/variant name, but it failed ValidName")
		}
	}
}

func TestSwitchVolume(t *testing.T) {
	currentVolume := "foo"
	basePath, err := ioutil.TempDir("", "switch")
	if err != nil {
		t.Errorf("Could not create TempDir: %s\n", err)
	}
	disableDockerIntegration := true
	dvol := NewDvolAPI(basePath, disableDockerIntegration)
	err = dvol.SwitchVolume(currentVolume)
	if err != nil {
		t.Errorf("SwitchVolume failed: %s\n", err)
	}
	activeVolume, err := dvol.ActiveVolume()
	if err != nil {
		t.Error("Could not find ActiveVolume")
	}
	if activeVolume != "foo" {
		t.Errorf("%s is not equal to 'foo'", activeVolume)
	}
}
