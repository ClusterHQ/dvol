package datalayer

import (
    "regexp"
)

// ClusterHQ data layer, naive vfs (directory-based) implementation

func ValidVolumeName(volumeName string) bool {
    var validVolumeRegex = regexp.MustCompile(`^[a-zA-Z]+[a-zA-Z0-9-]+$`)
    return validVolumeRegex.MatchString(volumeName)
}

func VolumeExists() {}
func CreateVolume() {}
func CreateVariant() {}
