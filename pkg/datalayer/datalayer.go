package datalayer

import (
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
)

const MAX_NAME_LENGTH int = 40

// ClusterHQ data layer, naive vfs (directory-based) implementation

func ValidName(name string) bool {
	var validNameRegex = regexp.MustCompile(`^[a-zA-Z]+[a-zA-Z0-9-]*$`)
	return validNameRegex.MatchString(name) && len(name) <= MAX_NAME_LENGTH
}

type DataLayer struct {
	BasePath string
}

func (dl *DataLayer) VolumeExists(volumeName string) bool {
	volumePath := filepath.FromSlash(dl.BasePath + "/" + volumeName)
	_, err := os.Stat(volumePath)
	return err == nil
}

func (dl *DataLayer) ActiveVolume() (string, error) {
	currentVolumeJsonPath := filepath.FromSlash(dl.BasePath + "/current_volume.json")
	file, err := os.Open(currentVolumeJsonPath)
	if err != nil {
		return "", err
	}
	defer file.Close()
	decoder := json.NewDecoder(file)
	var store map[string]interface{}
	err = decoder.Decode(&store)
	if err != nil {
		return "", err
	}
	return store["current_volume"].(string), nil
}

func (dl *DataLayer) setActiveVolume(volumeName string) error {
	currentVolumeJsonPath := filepath.FromSlash(dl.BasePath + "/current_volume.json")
	currentVolumeContent := map[string]string{
		"current_volume": volumeName,
	}
	// Create or update this file
	file, err := os.Create(currentVolumeJsonPath)
	if err != nil {
		return err
	}
	defer file.Close()
	encoder := json.NewEncoder(file)
	encoder.Encode(currentVolumeContent)
	return nil
}

func (dl *DataLayer) CreateVolume(volumeName string) error {
	volumePath := filepath.FromSlash(dl.BasePath + "/" + volumeName)
	// TODO Factor this into a data layer object.
	err := os.MkdirAll(volumePath, 0777) // XXX SEC
	if err != nil {
		return err
	}
	return dl.setActiveVolume(volumeName)
}

func (dl *DataLayer) RemoveVolume(volumeName string) error {
	volumePath := filepath.FromSlash(dl.BasePath + "/" + volumeName)
	return os.RemoveAll(volumePath)
}

func (dl *DataLayer) CreateVariant(volumeName, variantName string) error {
	// XXX Variants are meant to be tagged commits???
	variantPath := filepath.FromSlash(dl.BasePath + "/" + volumeName + "/branches/master")
	return os.MkdirAll(variantPath, 0777) // XXX SEC
}

func (dl *DataLayer) SwitchVolume(volumeName string) error {
	return dl.setActiveVolume(volumeName)
}

func (dl *DataLayer) CheckoutBranch(branchName string) error {
	return nil
}
