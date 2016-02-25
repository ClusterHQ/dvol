package datalayer

import (
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
