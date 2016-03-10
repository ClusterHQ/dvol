package datalayer

import (
	//"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"github.com/nu7hatch/gouuid"
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

func (dl *DataLayer) volumePath(volumeName string) string {
	return filepath.FromSlash(dl.BasePath + "/" + volumeName)
}

func (dl *DataLayer) branchPath(volumeName, branchName string) string {
	return filepath.FromSlash(dl.BasePath + "/" + volumeName + "/branches/" + branchName)
}

func (dl *DataLayer) commitPath(volumeName string, commitId CommitId) string {
	return filepath.FromSlash(dl.BasePath + "/" + volumeName + "/commits/" + string(commitId))
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
	uuid1, err := uuid.NewV4()
	if err != nil {
		return CommitId(""), err
	}
	uuid2, err := uuid.NewV4()
	if err != nil {
		return CommitId(""), err
	}
	commitId := CommitId(strings.Replace("-", "", string(uuid1[:])+string(uuid2[:]), -1)[:40])
	//branchPath := dl.branchPath(volumeName, variantName)
	//commitPath := dl.commitPath(volumeName, commitId)
	// TODO acquire lock
	// TODO check if commitPath exists, bail if not
	//dl.copyFiles(branchPath, commitPath)
	// TODO release lock
	return commitId, nil
}

/*
func (dl *DataLayer) ReadCommitsForBranch(volumeName, variantName string) ([]Commit, error) {
}

func (dl *DataLayer) WriteCommitsForBranch(volumeName, variantName string, commits []Commit) {
}
*/
