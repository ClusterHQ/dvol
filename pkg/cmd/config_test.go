package cmd

import (
	"os"
	"testing"

	"github.com/spf13/viper"
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
