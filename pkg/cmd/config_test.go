package cmd

import (
	"os"
	"testing"
)

func TestCannotGetYet(t *testing.T) { // TODO: Implement get and then remove this
	args := []string{"user.name"}

	if err := dispatchConfig(args, os.Stdout); err != nil {
		if err.Error() != "Any operation other than setting a value is not implemented yet." {
			t.Error("Unexpected error", err)
		}
	} else {
		t.Error("No error")
	}
}
