package datalayer

// TODO: Rename this & every other reference to 'datalayer' with 'dataplane'

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/nu7hatch/gouuid"
	git2go "gopkg.in/libgit2/git2go.v23"
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
	Name string
	Path string
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
	return filepath.FromSlash(dl.basePath + "/" + volumeName + "/commits/" + string(commitId))
}

// TODO: Rename to CreateDataset
func (dl *DataLayer) CreateVolume(volumeName string) error {
	volumePath := dl.volumePath(volumeName)
	err := os.MkdirAll(volumePath, 0777)
	if err != nil {
		return err
	}
	repo_path := "aoustnahoeustnaoehusnatheus"
	repo, err := git2go.InitRepository(repo_path, true)
	if err != nil {
		// TODO: Undo the MkdirAll
		return err
	}
	config, err := repo.Config()
	if err != nil {
		// TODO: Undo the MkdirAll and the bare repo creation
		return err
	}
	err = config.SetBool("http.receivepack", true)
	if err != nil {
		// TODO: Undo the mkdir, the bare repo creation
		return err
	}
	fp, err := os.Create(filepath.Join(repo_path, "git-daemon-export-ok"))
	if err != nil {
		// TODO: Undo the mkdir, delete the repo
		return err
	} else {
		// XXX: What should we do when the fp fails to close?
		return fp.Close()
	}
}

func (dl *DataLayer) RemoveVolume(volumeName string) error {
	volumePath := dl.volumePath(volumeName)
	return os.RemoveAll(volumePath)
}

func (dl *DataLayer) ResetVolume(commit, volumeName, variantName string) error {
	variantPath := dl.variantPath(volumeName, variantName)

	// TODO: If commit starts with 'HEAD', might be do-able in api
	var commitId CommitId
	var err error
	if strings.HasPrefix(commit, "HEAD") {
		commitId, err = dl.resolveNamedCommitOnBranch(commit, volumeName, variantName)
		if err != nil {
			return err
		}
	} else {
		commitId = CommitId(commit)
	}
	commitPath := dl.commitPath(volumeName, commitId)
	if _, err := os.Stat(commitPath); err != nil {
		return err
	}
	// TODO: Acquire lock
	if err := os.RemoveAll(variantPath); err != nil {
		return err
	}
	if err := dl.copyFiles(commitPath, variantPath); err != nil {
		return err
	}
	if err := dl.destroyNewerCommits(commitId, volumeName, variantName); err != nil {
		return err
	}
	// TODO: Release lock (should be deferred actually)
	return err
}

func (dl *DataLayer) CreateVariant(volumeName, variantName string) error {
	variantPath := dl.variantPath(volumeName, variantName)
	return os.MkdirAll(variantPath, 0777)
}

func (dl *DataLayer) CreateVariantFromVariant(volumeName, fromVariant, toVariant string) error {
	variantPath := dl.variantPath(volumeName, toVariant)
	head, err := dl.resolveNamedCommitOnBranch("HEAD", volumeName, fromVariant)
	if err != nil {
		return err
	}
	commits, err := dl.ReadCommitsForBranch(volumeName, fromVariant)
	if err != nil {
		return err
	}
	if err != dl.WriteCommitsForBranch(volumeName, toVariant, commits) {
		return err
	}
	headCommitPath := dl.commitPath(volumeName, head)
	if err := dl.copyFiles(headCommitPath, variantPath); err != nil {
		return err
	}
	return nil
}

func (dl *DataLayer) AllVariants(volumeName string) ([]string, error) {
	var variants []string
	branchesPath := filepath.FromSlash(dl.volumePath(volumeName) + "/branches")
	contents, err := ioutil.ReadDir(branchesPath)
	if err != nil {
		return variants, err
	}
	for _, file := range contents {
		if file.IsDir() {
			variants = append(variants, file.Name())
		}
	}
	return variants, nil
}

func (dl *DataLayer) VariantExists(volumeName, variantName string) bool {
	variantPath := dl.variantPath(volumeName, variantName)
	_, err := os.Stat(variantPath)
	return err == nil
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

var NoCommits = errors.New("No commits made on this variant yet")

func (dl *DataLayer) resolveNamedCommitOnBranch(commit, volumeName, variantName string) (CommitId, error) {
	remainder := commit[len("HEAD"):]
	var offset int
	if remainder == strings.Repeat("^", len(remainder)) {
		offset = len(remainder)
	} else {
		return "", fmt.Errorf("Malformed commit identifier %s", commit)
	}
	// Read the commit database
	commits, err := dl.ReadCommitsForBranch(volumeName, variantName)
	if err != nil {
		return CommitId(""), err
	}
	if len(commits) == 0 {
		return CommitId(""), NoCommits
	}
	return commits[len(commits)-1-offset].Id, nil
}

var NotFound = errors.New("Item not found")

func indexOfCommit(commitId CommitId, commits []Commit) (int, error) {
	for idx, commit := range commits {
		if commit.Id == commitId {
			return idx, nil
		}
	}
	return -1, NotFound
}

func (dl *DataLayer) allCommitsNotInVariant(volumeName, variantName string) (map[CommitId]Commit, error) {
	allCommits := make(map[CommitId]Commit)
	allVariants, err := dl.AllVariants(volumeName)
	if err != nil {
		return allCommits, err
	}
	for _, variant := range allVariants {
		if variant != variantName {
			variantCommits, err := dl.ReadCommitsForBranch(volumeName, variant)
			if err != nil {
				return allCommits, err
			}
			for _, commit := range variantCommits {
				allCommits[commit.Id] = commit
			}
		}
	}
	return allCommits, nil
}

func (dl *DataLayer) destroyCommits(volumeName string, destroy []Commit, all map[CommitId]Commit) error {
	for _, commit := range destroy {
		// If commit not referenced in another branch, destroy it
		if _, ok := all[commit.Id]; !ok {
			commitPath := dl.commitPath(volumeName, commit.Id)
			if err := os.RemoveAll(commitPath); err != nil {
				return err
			}
		}
	}
	return nil
}

func (dl *DataLayer) destroyNewerCommits(commitId CommitId, volumeName, variantName string) error {
	// TODO: This should really be atomic but it's okay for now
	commits, err := dl.ReadCommitsForBranch(volumeName, variantName)
	if err != nil {
		return err
	}
	commitIdx, err := indexOfCommit(commitId, commits)
	if err == NotFound {
		return fmt.Errorf("Could not find commit with ID %s\n", string(commitId))
	}
	remainingCommits := commits[:commitIdx+1]
	destroyCommits := commits[commitIdx+1:]
	allCommits, err := dl.allCommitsNotInVariant(volumeName, variantName)
	if err != nil {
		return err
	}
	if err := dl.destroyCommits(volumeName, destroyCommits, allCommits); err != nil {
		return err
	}
	if err := dl.WriteCommitsForBranch(volumeName, variantName, remainingCommits); err != nil {
		return err
	}
	return nil
}
