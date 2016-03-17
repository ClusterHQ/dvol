package api

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"

	"github.com/ClusterHQ/dvol/pkg/containers"
	"github.com/ClusterHQ/dvol/pkg/datalayer"
	"github.com/fsouza/go-dockerclient"
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
		client, _ := docker.NewClientFromEnv()
		containerRuntime = containers.DockerRuntime{client}
	} else {
		containerRuntime = containers.NoneRuntime{}
	}
	return &DvolAPI{options.BasePath, dl, containerRuntime}
}

func (dvol *DvolAPI) VolumePath(volumeName string) string {
	return dvol.dl.VolumeFromName(volumeName).Path
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
	if err := encoder.Encode(currentVolumeContent); err != nil {
		return err
	}
	return nil
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
	return nil
}

func (dvol *DvolAPI) CreateBranch(volumeName, branchName string) error {
	return dvol.dl.CreateVariant(volumeName, branchName)
}

var NotFound = errors.New("Item not found")

func indexOfVariant(variantName string, variants []string) (int, error) {
	for idx, variant := range variants {
		if variant == variantName {
			return idx, nil
		}
	}
	return -1, NotFound
}

func (dvol *DvolAPI) CheckoutBranch(volumeName, firstBranch, secondBranch string, create bool) error {
	if create {
		allVariants, err := dvol.dl.AllVariants(volumeName)
		if err != nil {
			return err
		}
		if _, err := indexOfVariant(secondBranch, allVariants); err == nil {
			return fmt.Errorf("Cannot create existing branch %s", secondBranch)
		}
		if err := dvol.dl.CreateVariantFromVariant(volumeName, firstBranch, secondBranch); err != nil {
			return err
		}
	} else {
		branchPath := dvol.dl.VariantPath(volumeName, secondBranch)
		if _, err := os.Stat(branchPath); err != nil {
			if os.IsNotExist(err) {
				return fmt.Errorf("Cannot switch to a non-existing branch %s\n", secondBranch)
			}
		}
	}
	if err := dvol.setActiveBranch(volumeName, secondBranch); err != nil {
		return err
	}
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
	return dvol.containerRuntime.Related(volumeName)
}

/*
func (dvol *DvolAPI) resolveNamedCommitOnActiveBranch(commit, volumeName string) (error, string) {
	// Get the active branch on the specified volume
	// Get the commit offset, returning an error if the commit name isn't correctly formed
	// Return the commit ID from the database
	currentBranch, err := dvol.ActiveBranch(volumeName)
	if err != nil {
		return err, ""
	}
	remainder := commit[len("HEAD"):]
	if remainder == strings.Repeat("^", len(remainder)) {
		offset := len(remainder)
	} else {
		return fmt.Errorf("Malformed commit identifier %s", commit), ""
	}
	// Read the commit database
	return nil, "" //commitId
}
*/
/*
func (dvol *DvolAPI) CreateBranchFromBranch(volumeName, branchName string) error {
	// Get the path to the volume and the branch
	// If we were asked to create it:
	// NEEDS TO BE DONE BY DATALAYER CREATEVARIANT
	// 	Get the HEAD, return an error regarding needing to commit if the HEAD doesn't exist yet
	// 	Copy the metadata from the active branch to the new branch
	// 	Copy the head commit (commits/deadbeef1234etc) into the new branch path
	branchPath := filepath.FromSlash(dvol.basePath + "/" + volumeName + "/branches/" + branchName)
	err, head := dvol.resolveNamedCommitOnActiveBranch("HEAD", volumeName)
	return err
}
*/
