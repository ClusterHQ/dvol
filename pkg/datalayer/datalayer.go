package datalayer

import (
	"encoding/json"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"
)

const MAX_VOLUME_NAME_LENGTH int = 40

// ClusterHQ data layer, naive vfs (directory-based) implementation

func ValidVolumeName(volumeName string) bool {
	var validVolumeRegex = regexp.MustCompile(`^[a-zA-Z]+[a-zA-Z0-9-]*$`)
	return validVolumeRegex.MatchString(volumeName) && len(volumeName) <= MAX_VOLUME_NAME_LENGTH
}

func VolumeExists(basePath string, volumeName string) bool {
	volumePath := filepath.FromSlash(basePath + "/" + volumeName)
	_, err := os.Stat(volumePath)
	return err == nil
}

func ActiveVolume(basePath string) (string, error) {
	currentVolumeJsonPath := filepath.FromSlash(basePath + "/current_volume.json")
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

func setActiveVolume(basePath, volumeName string) error {
	currentVolumeJsonPath := filepath.FromSlash(basePath + "/current_volume.json")
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

func CreateVolume(basePath string, volumeName string) error {
	volumePath := filepath.FromSlash(basePath + "/" + volumeName)
	// TODO Factor this into a data layer object.
	err := os.MkdirAll(volumePath, 0777) // XXX SEC
	if err != nil {
		return err
	}
	return setActiveVolume(basePath, volumeName)
}

func RemoveVolume(basePath string, volumeName string) error {
	volumePath := filepath.FromSlash(basePath + "/" + volumeName)
	return os.RemoveAll(volumePath)
}

func CreateVariant(basePath, volumeName, variantName string) error {
	// XXX Variants are meant to be tagged commits???
	variantPath := filepath.FromSlash(basePath + "/" + volumeName + "/branches/master")
	return os.MkdirAll(variantPath, 0777) // XXX SEC
}

func VolumeVariant(basePath, volumeName string) (string, error) {
	currentBranchJsonPath := filepath.FromSlash(basePath + "/" + volumeName + "/current_branch.json")
	file, err := os.Open(currentBranchJsonPath)
	if err != nil {
		// The error type should be checked here.
		// Only return master if no volume information is found.
		return "master", nil
	}
	defer file.Close()
	decoder := json.NewDecoder(file)
	var store map[string]interface{}
	err = decoder.Decode(&store)
	if err != nil {
		return "", err
	}
	return store["current_branch"].(string), nil
}

func AllVolumes(basePath string) ([]string, error) {
	files, err := ioutil.ReadDir(basePath)
	if err != nil {
		return []string{}, err
	}
	volumes := make([]string, 0)
	for _, file := range files {
		if file.IsDir() {
			volumes = append(volumes, file.Name())
		}
	}
	return volumes, nil
}

func SwitchVolume(basePath, volumeName string) error {
	return setActiveVolume(basePath, volumeName)
}
