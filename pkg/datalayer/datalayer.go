package datalayer

import (
	"encoding/json"
	"io/ioutil"
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


// XXX what follows may need to be factored out
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
