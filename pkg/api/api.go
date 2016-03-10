package api

import (
	"encoding/json"
	//	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"
	//	"strings"

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

func (dvol *DvolAPI) CreateBranch(volumeName, branchName string) error {
	return dvol.dl.CreateVariant(volumeName, branchName)
}

func (dvol *DvolAPI) SwitchBranch(volumeName, branchName string) error {
	return nil
}

func (dvol *DvolAPI) CheckoutBranch(volumeName, branchName string, create bool) error {
	// Get the path to the volume and the branch
	// If we were asked to create it:
	// NEEDS TO BE DONE BY DATALAYER CREATEVARIANT
	// 	Get the HEAD, return an error regarding needing to commit if the HEAD doesn't exist yet
	// 	Copy the metadata from the active branch to the new branch
	// 	Copy the head commit (commits/deadbeef1234etc) into the new branch path
	// Switch to it
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

func (dvol *Dvol) SwitchVolume(volumeName string) error {
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

func (dvol *DvolAPI) AllVolumes() ([]string, error) {
	files, err := ioutil.ReadDir(dvol.basePath)
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

func (dvol *DvolAPI) Commit(activeVolume, activeBranch, commitMessage string) {
	return dvol.dl.Snapshot(activeVolume, activeBranch, commitMessage)
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
