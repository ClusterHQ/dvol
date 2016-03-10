package datalayer

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
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
	Id      CommitId      `json:"id"`
	Message CommitMessage `json:"message"`
}

func NewDataLayer(basePath string) *DataLayer {
	return &DataLayer{basePath}
}

func (dl *DataLayer) volumePath(volumeName string) string {
	return filepath.FromSlash(dl.basePath + "/" + volumeName)
}

func (dl *DataLayer) variantPath(volumeName, variantName string) string {
	return filepath.FromSlash(dl.basePath + "/" + volumeName + "/branches/" + variantName)
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

func (dl *DataLayer) sanitizePath(path string) error {
	// Calculate that dl.basePath is a strict prefix of filepath.Clean(path)
	if !strings.HasPrefix(filepath.Clean(path), dl.basePath) {
		return fmt.Errorf("%s is not a prefix of %s", filepath.Clean(path), dl.basePath)
	}
	return nil
}

func (dl *DataLayer) copyFiles(from, to string) error {
	log.Print("copying", from, " to", to)
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
	cp, lookErr := exec.LookPath("cp")
	if lookErr != nil {
		panic(lookErr)
	}
	log.Print("running", "cp", "-a", from, " ", to)
	return syscall.Exec(cp, []string{"cp", "-a", from, to}, []string{})
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
	bigUUID := uuid1.String() + uuid2.String()
	// XXX why the hell isn't this working?
	bigUUID = strings.Replace("-", "", bigUUID, -1)
	commitId := CommitId(bigUUID[:40])
	log.Print("commit id is...", commitId)
	variantPath := dl.variantPath(volumeName, variantName)
	commitPath := dl.commitPath(volumeName, commitId)
	if _, err := os.Stat(commitPath); err == nil {
		return CommitId(""), fmt.Errorf("UUID collision. Please step out of the infinite improbability drive.")
	}
	commitsDir, _ := filepath.Split(commitPath)
	if err := os.MkdirAll(commitsDir, 0777); err != nil {
		return CommitId(""), err
	}
	// TODO acquire lock
	dl.copyFiles(variantPath, commitPath)
	// TODO release lock
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
	log.Print("Going to stat", branchDB)
	_, err := os.Stat(branchDB)
	if err == nil {
		// File doesn't exist, so it's an empty database.
		return []Commit{}, nil
	}
	log.Print("err was nil")
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
