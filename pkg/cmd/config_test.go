package cmd

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"os"
	"reflect"
	"testing"

	"github.com/spf13/viper"
	"gopkg.in/yaml.v2"
)

func TestMain(m *testing.M) {
	var err error
	basePath, err = ioutil.TempDir("", "dvol_config_test")
	if err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
	defer os.RemoveAll(basePath)
	os.Exit(m.Run())
}

func TestNoOperationSpecified(t *testing.T) {
	args := []string{}
	listAll = false
	if err := dispatchConfig(args, os.Stdout); err == nil {
		t.Error("No error")
	} else if err.Error() != "No operation specified" {
		t.Error("Unexpected error:", err)
	}
}

func TestTooManyArguments(t *testing.T) {
	args := []string{"first", "second", "third"}

	if err := dispatchConfig(args, os.Stdout); err == nil {
		t.Error("No error")
	} else if err.Error() != "Too many arguments" {
		t.Error("Unexpected error:", err)
	}
}

func TestMissingConfig(t *testing.T) {
	// Initialising the configuration when it is missing is not an error
	os.Remove(configPath())
	if err := initialiseConfig(); err != nil {
		t.Error(err)
	}
}

func TestSetConfigValue(t *testing.T) {
	// Providing two arguments will store a value that can be read from the
	// config store
	viper.Reset()

	args := []string{"user.name", "alice"}
	if err := dispatchConfig(args, os.Stdout); err != nil {
		t.Error(err)
	}

	value := viper.GetString("user.name")
	if value != "alice" {
		t.Error("Incorrect value retrieved, got:", value)
	}
}

func TestSetUnknownValue(t *testing.T) {
	// Only known keys can be stored
	viper.Reset()

	args := []string{"garbage", "garbage"}
	if err := dispatchConfig(args, os.Stdout); err == nil {
		t.Error("No error")
	} else if err.Error() != "'garbage' is not a valid configuration key" {
		t.Error("Unexpected error:", err)
	}
}

func TestUnmarshal(t *testing.T) {
	// The config can be unmarshaled into a struct
	if err := setConfigValue("user.name", "alice"); err != nil {
		t.Error(err)
	}

	config, err := unmarshalConfig()
	if err != nil {
		t.Error(err)
	}
	expected := Config{
		UserName: "alice",
	}
	if !reflect.DeepEqual(config, expected) {
		t.Error("Not equal:", config, expected)
	}
}

func TestMarshal(t *testing.T) {
	// A Config struct can be marshaled into YAML bytes
	config := Config{
		UserName:  "alice",
		UserEmail: "alice@acme.co",
	}
	expected := []byte(`user.name: alice
user.email: alice@acme.co
`)

	out, err := yaml.Marshal(config)
	if err != nil {
		t.Error(err)
	}
	if !bytes.Equal(out, expected) {
		t.Error("\nExpected:\t", expected, "\nGot:\t\t", out)
	}
}

func TestConfigFileMode(t *testing.T) {
	// The config is saved as readable and writeable by the user only
	viper.Reset()
	if err := setConfigValue("user.name", "alice"); err != nil {
		t.Error(err)
	}

	configPath := configPath()
	stat, err := os.Stat(configPath)
	if err != nil {
		t.Error(err)
	}
	perm := stat.Mode().Perm()
	if perm != 0600 {
		t.Error("Incorrect permissions", perm, "on", configPath)
	}
}

func TestConfigReadFromDisk(t *testing.T) {
	// The config is readable after being written
	viper.Reset()
	if err := setConfigValue("user.name", "alice"); err != nil {
		t.Error(err)
	}

	initialiseConfig()

	value := viper.GetString("user.name")
	if value != "alice" {
		t.Error("Incorrect value retrieved, got:", value)
	}
}

func TestConfigGetOutput(t *testing.T) {
	// Passing only a single argument results in the configuration key value
	// being printed to Stdout followed by a newline.
	viper.Reset()
	if err := setConfigValue("user.name", "alice"); err != nil {
		t.Error(err)
	}

	args := []string{"user.name"}
	w := new(bytes.Buffer)

	if err := dispatchConfig(args, w); err != nil {
		t.Error(err)
	}

	outString := w.String()
	if outString != "alice\n" {
		t.Errorf("Unexpected output, got: %v, expected: %v", outString, "alice\n")
	}
}

func TestConfigGetOutputEmpty(t *testing.T) {
	// Passing only a single argument results in the configuration key value
	// being printed to Stdout followed by a newline. If the key is unset or empty, print nothing.
	viper.Reset()
	args := []string{"user.name"}
	w := new(bytes.Buffer)

	if err := dispatchConfig(args, w); err != nil {
		t.Error(err)
	}

	out := w.String()
	if out != "" {
		t.Errorf("Unexpected output, got: %v, expected: %v", out, "alice\n")
	}
}

func TestListConfig(t *testing.T) {
	viper.Reset()
	setConfigValue("user.name", "alice")
	setConfigValue("user.email", "alice@acme.co")

	args := []string{}
	listAll = true
	w := new(bytes.Buffer)

	if err := dispatchConfig(args, w); err != nil {
		t.Error(err)
	}

	out := w.String()
	expected := `user.name=alice
user.email=alice@acme.co
`

	if out != expected {
		t.Errorf("Unexpected output, got: %v, expected: %v", out, expected)
	}
}

func TestListConfigMissingKey(t *testing.T) {
	// Print the keys which are missing, this will aid the user in discovering
	// what they can set
	viper.Reset()
	setConfigValue("user.name", "alice")
	setConfigValue("user.email", "")

	args := []string{}
	listAll = true
	w := new(bytes.Buffer)

	if err := dispatchConfig(args, w); err != nil {
		t.Error(err)
	}

	out := w.String()
	expected := `user.name=alice
user.email=
`

	if out != expected {
		t.Errorf("Unexpected output, got: %v, expected: %v", out, expected)
	}
}
