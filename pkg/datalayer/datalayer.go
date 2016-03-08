package datalayer

import (
	"os"
	"path/filepath"
)

// ClusterHQ data layer, naive vfs (directory-based) implementation

type DataLayer struct {
	BasePath string
}

func (dl *DataLayer) CreateVolume(volumeName string) error {
	volumePath := filepath.FromSlash(dl.BasePath + "/" + volumeName)
	// TODO Factor this into a data layer object.
	err := os.MkdirAll(volumePath, 0777) // XXX SEC
	if err != nil {
		return err
	}
	return nil
}

func (dl *DataLayer) RemoveVolume(volumeName string) error {
	volumePath := filepath.FromSlash(dl.BasePath + "/" + volumeName)
	return os.RemoveAll(volumePath)
}

func (dl *DataLayer) CreateVariant(volumeName, variantName string) error {
	// XXX Variants are meant to be tagged commits???
	variantPath := filepath.FromSlash(dl.BasePath + "/" + volumeName + "/branches/" + variantName)
	return os.MkdirAll(variantPath, 0777) // XXX SEC
}
