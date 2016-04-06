package cmd

import (
	"bytes"
	"os"
	"reflect"
	"testing"

	"github.com/spf13/viper"
	"gopkg.in/yaml.v2"
)

func TestCannotGetYet(t *testing.T) { // TODO: Implement get and then remove this
	args := []string{"user.name"}

	if err := dispatchConfig(args, os.Stdout); err == nil {
		t.Error("No error")
	} else if err.Error() != "Any operation other than setting a value is not implemented yet" {
		t.Error("Unexpected error:", err)
	}
}

func TestNotEnoughArguments(t *testing.T) {
	args := []string{}

	if err := dispatchConfig(args, os.Stdout); err == nil {
		t.Error("No error")
	} else if err.Error() != "Not enough arguments" {
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
		UserName: "alice",
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
