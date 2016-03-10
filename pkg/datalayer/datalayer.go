package datalayer

import (
	//"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"syscall"

	"github.com/nu7hatch/gouuid"
)

// ClusterHQ data layer, naive vfs (directory-based) implementation

type DataLayer struct {
	basePath string
}

type CommitId string
type CommitMessage string

type Commit struct {
	Id      CommitId
	Message CommitMessage
}

func NewDataLayer(basePath string) *DataLayer {
	return &DataLayer{basePath}
}

func (dl *DataLayer) volumePath(volumeName string) string {
	return filepath.FromSlash(dl.basePath + "/" + volumeName)
}

func (dl *DataLayer) branchPath(volumeName, branchName string) string {
	return filepath.FromSlash(dl.basePath + "/" + volumeName + "/branches/" + branchName)
}

func (dl *DataLayer) commitPath(volumeName string, commitId CommitId) string {
	return filepath.FromSlash(dl.basePath + "/" + volumeName + "/commits/" + string(commitId))
}

func (dl *DataLayer) CreateVolume(volumeName string) error {
	volumePath := dl.volumePath(volumeName)
	return os.MkdirAll(volumePath, 0777)
}

func (dl *DataLayer) RemoveVolume(volumeName string) error {
	volumePath := filepath.FromSlash(dl.basePath + "/" + volumeName)
	return os.RemoveAll(volumePath)
}

func (dl *DataLayer) CreateVariant(volumeName, variantName string) error {
	// XXX Variants are meant to be tagged commits???
	variantPath := filepath.FromSlash(dl.basePath + "/" + volumeName + "/branches/" + variantName)
	return os.MkdirAll(variantPath, 0777)
}

func (dl *DataLayer) sanitizePath(path) error {
	// Calculate that dl.basePath is a strict prefix of filepath.Clean(path)
	if !strings.HasPrefix(filePath.Clean(path), dl.basePath) {
		return fmt.Errorf("%s is not a prefix of %s", filepath.Clean(path), dl.basePath)
	}
	return nil
}

func (dl *DataLayer) copyFiles(from, to) error {
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
	_, err := os.Stat(to)
	if err == nil {
		return fmt.Errorf("%s already exists", to)
	}
	cp, lookErr := exec.LookPath("cp")
	if lookErr != nil {
		panic(lookErr)
	}
	return syscall.Exec(cp, []string{"cp", "-a", from, to})
}

func (dl *DataLayer) Snapshot(volumeName, variantName, commitMessage string) (CommitId, error) {
	uuid1, err := uuid.NewV4()
	if err != nil {
		return CommitId(""), err
	}
	uuid2, err := uuid.NewV4()
	if err != nil {
		return CommitId(""), err
	}
	commitId := CommitId(strings.Replace("-", "", string(uuid1[:])+string(uuid2[:]), -1)[:40])
	branchPath := dl.branchPath(volumeName, variantName)
	commitPath := dl.commitPath(volumeName, commitId)
	if _, err := os.Stat(commitPath); err == nil {
		return CommitId(), fmt.Errorf("UUID collision. Please step out of the infinite improbability drive.")
	}
	// TODO acquire lock
	dl.copyFiles(branchPath, commitPath)
	// TODO release lock
	return commitId, nil
}

/*
func (dl *DataLayer) ReadCommitsForBranch(volumeName, variantName string) ([]Commit, error) {
}

func (dl *DataLayer) WriteCommitsForBranch(volumeName, variantName string, commits []Commit) {
}
*/
