package containers

import (
	"testing"

	"github.com/fsouza/go-dockerclient"
)

func TestIsRelatedNoMounts(t *testing.T) {
	var c docker.Container
	c.Mounts = make([]docker.Mount, 0)
	if isRelated("volume_name", &c) {
		t.Error("Expected isRelated to be false for no mounts")
	}
}

func TestIsRelatedVolumeNameDifferent(t *testing.T) {
	var c docker.Container
	c.Mounts = make([]docker.Mount, 0)
	mount := docker.Mount{
		"volume_name", "source", "destination", "dvol", "mode", true,
	}
	c.Mounts = append(c.Mounts, mount)
	if isRelated("different_volume_name", &c) {
		t.Error("Expected isRelated to be false for different volume name")
	}
}

func TestIsRelatedDriverDifferent(t *testing.T) {
	var c docker.Container
	c.Mounts = make([]docker.Mount, 0)
	mount := docker.Mount{
		"volume_name", "source", "destination", "another_driver", "mode", true,
	}
	c.Mounts = append(c.Mounts, mount)
	if isRelated("volume_name", &c) {
		t.Error("Expected isRelated to be false for different driver")
	}
}

func TestIsRelated(t *testing.T) {
	var c docker.Container
	c.Mounts = make([]docker.Mount, 0)
	mount := docker.Mount{
		"volume_name", "source", "destination", "dvol", "mode", true,
	}
	c.Mounts = append(c.Mounts, mount)
	if !isRelated("volume_name", &c) {
		t.Error("Expected isRelated to be false for different driver")
	}
}
