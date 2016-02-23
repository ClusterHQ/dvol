package datalayer

import (
    "regexp"
)
const MAX_VOLUME_NAME_LENGTH int = 40
// ClusterHQ data layer, naive vfs (directory-based) implementation

func ValidVolumeName(volumeName string) bool {
    var validVolumeRegex = regexp.MustCompile(`^[a-zA-Z]+[a-zA-Z0-9-]*$`)
    return validVolumeRegex.MatchString(volumeName) && len(volumeName) <= MAX_VOLUME_NAME_LENGTH
}

func VolumeExists(volumeName string) bool {
    return true
}

func CreateVolume(volumeName string) error {

            // TODO Factor this into a data layer object.
            //os.MkdirAll(filepath.FromSlash(
            //    basePath + "/" + volumeName), 0777) // XXX SEC
    return nil
}
func CreateVariant(volumeName, variantName string) error {
    // XXX Variants are meant to be tagged commits???
            //os.MkdirAll(filepath.FromSlash(
            //    basePath + "/" + volumeName + "/branches/master"), 0777) // XXX SEC
    return nil
}
