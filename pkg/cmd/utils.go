package cmd

import (
	"fmt"
	"strings"
)

func checkVolumeArgs(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("Please specify a volume name.")
	}
	if len(args) > 1 {
		return fmt.Errorf("Wrong number of arguments.")
	}
	return nil
}

func userIsSure(extraMessage string) bool {
	message := fmt.Sprintf("Are you sure? %s (y/n): ", extraMessage)
	fmt.Print(message)
	var response string
	_, err := fmt.Scanln(&response)
	if err != nil {
		fmt.Println("Error reading response.")
		return false
	}
	response = strings.ToLower(response)
	if response == "y" || response == "yes" {
		return true
	}
	return false
}
