package datalayer

import (
	//"encoding/json"
	"github.com/nu7hatch/gouuid"

	"os"
	"path/filepath"
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

func (dl *DataLayer) CreateVolume(volumeName string) error {
	volumePath := filepath.FromSlash(dl.BasePath + "/" + volumeName)
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

func foo() {
	u4, err := uuid.NewV4()
	if err != nil {
		fmt.Println("error:", err)
		return
	}
	fmt.Println(u4)
}

/*
func (dl *DataLayer) ReadCommitsForBranch(volumeName, variantName string) ([]Commit, error) {
}

func (dl *DataLayer) WriteCommitsForBranch(volumeName, variantName string, commits []Commit) {
}
*/
