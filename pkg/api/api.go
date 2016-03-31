package api

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"

	"github.com/ClusterHQ/dvol/pkg/containers"
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

A data layer volume is what we call a writeable working copy.

current directory structure
---------------------------

What should go where?

STRUCTURE                                   WHAT
------------------------------------------------
current_volume.json                         dvol api
volumes/
  foo/
    current_branch.json                     dvol api
	running_point -> branches/bar           dvol docker integration
	commits/                                data layer commits
	  deadbeefdeadbeef/
	    <copy of data>
	branches/
	  bar/                                  data layer volume (one per branch), writeable working copy
	    <writeable data>
	  bar.json                              data layer commit metadata database (currently per branch, should be migrated into commits eventually, but not yet)

*/

const MAX_NAME_LENGTH int = 40
const DEFAULT_BRANCH string = "master"

func ValidName(name string) bool {
	var validNameRegex = regexp.MustCompile(`^[a-zA-Z]+[a-zA-Z0-9-]*$`)
	return validNameRegex.MatchString(name) && len(name) <= MAX_NAME_LENGTH
}

type DvolAPI struct {
	basePath         string
	dl               *datalayer.DataLayer
	containerRuntime containers.Runtime
}

type DvolVolume struct {
	// Represents a dvol volume
	Name string
	Path string
}

type DvolAPIOptions struct {
	BasePath                 string
	DisableDockerIntegration bool
}

func NewDvolAPI(options DvolAPIOptions) *DvolAPI {
	dl := datalayer.NewDataLayer(options.BasePath)
	var containerRuntime containers.Runtime
	if !options.DisableDockerIntegration {
		containerRuntime = containers.NewDockerRuntime()
	} else {
		containerRuntime = containers.NewNoneRuntime()
	}
	return &DvolAPI{options.BasePath, dl, containerRuntime}
}

func (dvol *DvolAPI) VolumePath(volumeName string) string {
	return filepath.FromSlash(dvol.dl.VolumeFromName(volumeName).Path + "/running_point")
}

func (dvol *DvolAPI) CreateVolume(volumeName string) error {
	err := dvol.dl.CreateVolume(volumeName)
	if err != nil {
		return err
	}

	if err = dvol.CreateBranch(volumeName, DEFAULT_BRANCH); err != nil {
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
	return encoder.Encode(currentVolumeContent)
}

func (dvol *DvolAPI) updateRunningPoint(volume datalayer.Volume, branchName string) error {
	branchPath := dvol.dl.VariantPath(volume.Name, branchName)
	stablePath := filepath.FromSlash(volume.Path + "/running_point")
	if _, err := os.Stat(stablePath); err == nil {
		if err := os.Remove(stablePath); err != nil {
			return err
		}
	}
	return os.Symlink(branchPath, stablePath)
}

func (dvol *DvolAPI) setActiveBranch(volumeName, branchName string) error {
	volume := dvol.dl.VolumeFromName(volumeName)
	currentBranchJsonPath := filepath.FromSlash(volume.Path + "/current_branch.json")
	currentBranchContent := map[string]string{
		"current_branch": branchName,
	}
	file, err := os.Create(currentBranchJsonPath)
	if err != nil {
		return err
	}
	defer file.Close()
	encoder := json.NewEncoder(file)
	if err := encoder.Encode(currentBranchContent); err != nil {
		return err
	}
	if err := dvol.containerRuntime.Stop(volumeName); err != nil {
		return err
	}
	if err := dvol.updateRunningPoint(volume, branchName); err != nil {
		return err
	}
	return dvol.containerRuntime.Start(volumeName)
}

func (dvol *DvolAPI) CreateBranch(volumeName, branchName string) error {
	return dvol.dl.CreateVariant(volumeName, branchName)
}

func (dvol *DvolAPI) CheckoutBranch(volumeName, sourceBranch, newBranch string, create bool) error {
	if create {
		if dvol.dl.VariantExists(volumeName, newBranch) {
			return fmt.Errorf("Cannot create existing branch %s", newBranch)
		}
		if err := dvol.dl.CreateVariantFromVariant(volumeName, sourceBranch, newBranch); err != nil {
			return err
		}
	} else {
		if !dvol.dl.VariantExists(volumeName, newBranch) {
			return fmt.Errorf("Cannot switch to a non-existing branch %s", newBranch)
		}
	}
	return dvol.setActiveBranch(volumeName, newBranch)
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
	volumePath := dvol.VolumePath(volumeName)
	_, err := os.Stat(volumePath)
	return err == nil
}

func (dvol *DvolAPI) SwitchVolume(volumeName string) error {
	return dvol.setActiveVolume(volumeName)
}

func (dvol *DvolAPI) ActiveBranch(volumeName string) (string, error) {
	currentBranchJsonPath := filepath.FromSlash(dvol.basePath + "/" + volumeName + "/current_branch.json")
	file, err := os.Open(currentBranchJsonPath)
	if err != nil {
		// The error type should be checked here.
		// Only return master if no volume information is found.
		return DEFAULT_BRANCH, nil
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

func (dvol *DvolAPI) AllBranches(volumeName string) ([]string, error) {
	return dvol.dl.AllVariants(volumeName)
}

func (dvol *DvolAPI) AllVolumes() ([]DvolVolume, error) {
	files, err := ioutil.ReadDir(dvol.basePath)
	if err != nil {
		return []DvolVolume{}, err
	}
	volumes := make([]DvolVolume, 0)
	for _, file := range files {
		if file.IsDir() {
			volumes = append(volumes, DvolVolume{
				Name: file.Name(),
				Path: dvol.VolumePath(file.Name()),
			})
		}
	}
	return volumes, nil
}

func (dvol *DvolAPI) Commit(activeVolume, activeBranch, commitMessage string) (string, error) {
	// returns a CommitId which is a string 40 byte UUID
	commitId, err := dvol.dl.Snapshot(activeVolume, activeBranch, commitMessage)
	if err != nil {
		return "", err
	}
	return string(commitId), nil
}

func (dvol *DvolAPI) ListCommits(activeVolume, activeBranch string) ([]datalayer.Commit, error) {
	return dvol.dl.ReadCommitsForBranch(activeVolume, activeBranch)
}

func (dvol *DvolAPI) ResetActiveVolume(commit string) error {
	activeVolume, err := dvol.ActiveVolume()
	if err != nil {
		return err
	}
	activeBranch, err := dvol.ActiveBranch(activeVolume)
	if err := dvol.dl.ResetVolume(commit, activeVolume, activeBranch); err != nil {
		return err
	}
	return nil
}

func (dvol *DvolAPI) RelatedContainers(volumeName string) ([]string, error) {
	containerNames := make([]string, 0)
	relatedContainers, err := dvol.containerRuntime.Related(volumeName)
	if err != nil {
		return containerNames, err
	}
	for _, container := range relatedContainers {
		containerNames = append(containerNames, string(container.Name))
	}
	return containerNames, nil
}
