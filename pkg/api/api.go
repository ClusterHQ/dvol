package api

import (
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"

	"github.com/ClusterHQ/dvol/pkg/datalayer"
)

/*
User
 | "dvol checkout -b foo"
 v
CLI
 | "what is the current active volume?", "oh, it's 'bar'"
 | "create branch 'foo' from active volume 'bar'"
 v
internal API
 | "create variant from snapshot at tip of volume bar"
 v
DataLayer (swappable for another implementation)

*/

/*

A dvol volume is:

* a forest of snapshots (aka commits, immutable snapshots of the volume at a certain point in time), with inherited branch labels
* a set of writeable working copies (writeable paths which get mounted into the container), one per branch

*/

const MAX_NAME_LENGTH int = 40

func ValidName(name string) bool {
	var validNameRegex = regexp.MustCompile(`^[a-zA-Z]+[a-zA-Z0-9-]*$`)
	return validNameRegex.MatchString(name) && len(name) <= MAX_NAME_LENGTH
}

type DvolAPI struct {
	basePath string
	dl       *datalayer.DataLayer
}

func NewDvolAPI(basePath string) *DvolAPI {
	dl := &datalayer.DataLayer{BasePath: basePath}
	return &DvolAPI{basePath, dl}
}

func (dvol *DvolAPI) CreateVolume(volumeName string) error {
	err := dvol.dl.CreateVolume(volumeName)
	if err != nil {
		return err
	}
	return dvol.setActiveVolume(volumeName)
}

func (dvol *DvolAPI) RemoveVolume(volumeName string) error {
	return dvol.dl.RemoveVolume(volumeName)
}

func (dvol *DvolAPI) setActiveVolume(volumeName string) error {
	currentVolumeJsonPath := filepath.FromSlash(dvol.basePath + "/current_volume.json")
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

func (dvol *DvolAPI) CreateVariant(volumeName, variantName string) error {
	return dvol.dl.CreateVariant(volumeName, variantName)
}

func (dvol *DvolAPI) setActiveVariant(volumeName, variantName string) error {
	return nil
}

func (dvol *DvolAPI) ActiveVolume() (string, error) {
	currentVolumeJsonPath := filepath.FromSlash(dvol.basePath + "/current_volume.json")
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

func (dvol *DvolAPI) VolumeExists(volumeName string) bool {
	volumePath := filepath.FromSlash(dvol.basePath + "/" + volumeName)
	_, err := os.Stat(volumePath)
	return err == nil
}

func (dvol *DvolAPI) SwitchVolume(volumeName string) error {
	return dvol.setActiveVolume(volumeName)
}
