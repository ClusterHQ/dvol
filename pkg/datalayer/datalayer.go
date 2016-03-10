package datalayer

import (
	//"encoding/json"

	"github.com/nu7hatch/gouuid"
	"os"
	"path/filepath"
	"strings"
)

// ClusterHQ data layer, naive vfs (directory-based) implementation

type DataLayer struct {
	BasePath string
}

type CommitId string
type CommitMessage string

type Commit struct {
	Id      CommitId
	Message CommitMessage
}

func (dl *DataLayer) volumePath(volumeName string) {
	return filepath.FromSlash(dl.BasePath + "/" + volumeName)
}

func (dl *DataLayer) branchPath(volumeName, branchName string) {
	return filepath.FromSlash(dl.BasePath + "/" + volumeName + "/branches/" + branchName)
}

func (dl *DataLayer) commitPath(volumeName string, commitId CommitId) {
	return filepath.FromSlash(dl.BasePath + "/" + volumeName + "/commits/" + commitId)
}

func (dl *DataLayer) CreateVolume(volumeName string) error {
	volumePath := dl.volumePath(volumeName)
	return os.MkdirAll(volumePath, 0777)
}

func (dl *DataLayer) RemoveVolume(volumeName string) error {
	volumePath := filepath.FromSlash(dl.BasePath + "/" + volumeName)
	return os.RemoveAll(volumePath)
}

func (dl *DataLayer) CreateVariant(volumeName, variantName string) error {
	// XXX Variants are meant to be tagged commits???
	variantPath := filepath.FromSlash(dl.BasePath + "/" + volumeName + "/branches/" + variantName)
	return os.MkdirAll(variantPath, 0777)
}

func (dl *DataLayer) Snapshot(volumeName, variantName, commitMessage string) (CommitId, error) {
	commitId := strings.Replace("-", "", gouuid.NewV4()+gouuid.NewV4(), -1)[:40] // TODO type cast this?
	branchPath := dl.branchPath(branchName)
	commitPath := dl.commitPath(commitId)
	// TODO acquire lock
	// TODO check if commitPath exists, bail if not
	dl.copyFiles(branchPath, commitPath)
	// TODO release lock
	return nil, commitId
}

/*
func (dl *DataLayer) ReadCommitsForBranch(volumeName, variantName string) ([]Commit, error) {
}

func (dl *DataLayer) WriteCommitsForBranch(volumeName, variantName string, commits []Commit) {
}
*/
