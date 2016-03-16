package datalayer

import (
	"io/ioutil"
	"os"
	"testing"
)

func writeFile(path, content string) error {
	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()
	if _, err := file.WriteString(content); err != nil {
		return err
	}
	return nil
}

func readFile(path string) (string, error) {
	file, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer file.Close()
	contents := make([]byte, 5)
	_ = "breakpoint"
	num, err := file.Read(contents)
	if err != nil {
		return "", err
	}
	return string(contents[:num]), nil

}

func TestCreateVariantFromVariant(t *testing.T) {
	tempdir, err := ioutil.TempDir("", "datalayer")
	if err != nil {
		t.Error("Could not create temp directory")
	}
	dl := NewDataLayer(tempdir)
	// TODO: Create a volume foo
	if err := dl.CreateVolume("foo"); err != nil {
		t.Error("Could not create volume foo")
	}
	if err := dl.CreateVariant("foo", "master"); err != nil {
		t.Error("Could not create master variant")
	}
	// Put something in the master variant
	masterPath := dl.VariantPath("foo", "master")
	if err := writeFile(masterPath+"/file.txt", "alpha"); err != nil {
		t.Errorf("Failed to write to %s\n", masterPath)
	}
	if _, err := dl.Snapshot("foo", "master", "alphamessage"); err != nil {
		t.Error("Failed to snapshot variant master on volume foo")
	}
	_ = "breakpoint"
	if err := dl.CreateVariantFromVariant("foo", "master", "alpha"); err != nil {
		t.Error(err)
	}
	alphaFile := dl.VariantPath("foo", "alpha") + "/file.txt"
	alphaContents, err := readFile(alphaFile)
	if err != nil {
		t.Errorf("Could not read contents of %s\n", alphaFile)
	}
	if alphaContents != "alpha" {
		t.Errorf("%s != 'alpha'", alphaContents)
	}
	// TODO: Assert that variant 'beta' has the same content as variant 'alpha'
}
