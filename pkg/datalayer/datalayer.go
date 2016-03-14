package datalayer

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/nu7hatch/gouuid"
)

// ClusterHQ data layer, naive vfs (directory-based) implementation

type DataLayer struct {
	basePath string
}

type CommitId string
type CommitMessage string

type Commit struct {
	Id      CommitId      `json:"id"`
	Message CommitMessage `json:"message"`
}

type Volume struct {
	Name	string
	Path	string
}

func NewDataLayer(basePath string) *DataLayer {
	return &DataLayer{filepath.Clean(basePath)}
}

func (dl *DataLayer) volumePath(volumeName string) string {
	return filepath.FromSlash(dl.basePath + "/" + volumeName)
}

func (dl *DataLayer) VolumeFromName(volumeName string) Volume {
	return Volume{
		Name: volumeName,
		Path: dl.volumePath(volumeName),
	}
}

func (dl *DataLayer) variantPath(volumeName, variantName string) string {
	return filepath.FromSlash(dl.basePath + "/" + volumeName + "/branches/" + variantName)
}

func (dl *DataLayer) commitPath(volumeName string, commitId CommitId) string {
	return filepath.FromSlash(dl.basePath + "/" + volumeName + "/commits/" + commitId)
}

func (dl *DataLayer) CreateVolume(volumeName string) error {
	volumePath := dl.volumePath(volumeName)
	return os.MkdirAll(volumePath, 0777)
}

func (dl *DataLayer) RemoveVolume(volumeName string) error {
	volumePath := dl.volumePath(volumeName)
	return os.RemoveAll(volumePath)
}

func (dl *DataLayer) CreateVariant(volumeName, variantName string) error {
	variantPath := dl.variantPath(volumeName, variantName)
	return os.MkdirAll(variantPath, 0777)
}

func (dl *DataLayer) sanitizePath(path string) error {
	// Calculate that dl.basePath is a strict prefix of filepath.Clean(path)
	if !strings.HasPrefix(filepath.Clean(path), dl.basePath) {
		return fmt.Errorf("%s is not a prefix of %s", filepath.Clean(path), dl.basePath)
	}
	return nil
}

func (dl *DataLayer) copyFiles(from, to string) error {
	if err := dl.sanitizePath(from); err != nil {
		return err
	}
	if err := dl.sanitizePath(to); err != nil {
		return err
	}

	// check that ``from`` exists
	sourceFile, err := os.Stat(from)
	if err != nil {
		return err
	}
	if !sourceFile.Mode().IsDir() {
		return fmt.Errorf("%s is not a directory", from)
	}
	// check that ``to`` does not exist
	_, err = os.Stat(to)
	if err == nil {
		return fmt.Errorf("%s already exists", to)
	}
	cmd := exec.Command("cp", "-a", from, to)
	err = cmd.Run()
	if err != nil {
		return err
	}
	return err
}

func (dl *DataLayer) Snapshot(volumeName, variantName, commitMessage string) (CommitId, error) {
	// TODO: also accept timestamp, user data
	uuid1, err := uuid.NewV4()
	if err != nil {
		return CommitId(""), err
	}
	uuid2, err := uuid.NewV4()
	if err != nil {
		return CommitId(""), err
	}
	bigUUID := uuid1.String() + uuid2.String()
	bigUUID = strings.Replace(bigUUID, "-", "", -1)
	commitId := CommitId(bigUUID[:40])
	variantPath := dl.variantPath(volumeName, variantName)
	commitPath := dl.commitPath(volumeName, commitId)
	_, err = os.Stat(commitPath)
	if err != nil && !os.IsNotExist(err) {
		// Something bad happened (e.g. directory unreadable). Just return the error.
		return CommitId(""), err
	}
	if err == nil {
		return CommitId(""), fmt.Errorf("UUID collision. Please step out of the infinite improbability drive.")
	}
	commitsDir, _ := filepath.Split(commitPath)
	if err := os.MkdirAll(commitsDir, 0777); err != nil {
		return CommitId(""), err
	}
	// TODO acquire lock (docker integration)
	if err := dl.copyFiles(variantPath, commitPath); err != nil {
		return CommitId(""), err
	}
	// TODO release lock (docker integration)
	if err := dl.recordCommit(volumeName, variantName, commitMessage, commitId); err != nil {
		return CommitId(""), err
	}
	return commitId, nil
}

func (dl *DataLayer) recordCommit(volumeName, variantName, message string, commitId CommitId) error {
	commits, err := dl.ReadCommitsForBranch(volumeName, variantName)
	if err != nil {
		return err
	}
	commits = append(commits, Commit{Id: commitId, Message: CommitMessage(message)})
	return dl.WriteCommitsForBranch(volumeName, variantName, commits)
}

func (dl *DataLayer) ReadCommitsForBranch(volumeName, variantName string) ([]Commit, error) {
	branchDB := dl.variantPath(volumeName, variantName) + ".json"
	_, err := os.Stat(branchDB)
	if err != nil {
		// File doesn't exist, so it's an empty database.
		return []Commit{}, nil
	}
	// TODO factor this out
	file, err := os.Open(branchDB)
	if err != nil {
		return []Commit{}, err
	}
	defer file.Close()

	decoder := json.NewDecoder(file)
	var store []Commit
	err = decoder.Decode(&store)
	if err != nil {
		return []Commit{}, err
	}
	return store, nil
}

func (dl *DataLayer) WriteCommitsForBranch(volumeName, variantName string, commits []Commit) error {
	branchDB := dl.variantPath(volumeName, variantName) + ".json"
	file, err := os.Create(branchDB)
	if err != nil {
		return err
	}
	defer file.Close()
	encoder := json.NewEncoder(file)
	encoder.Encode(commits)
	return nil
}
