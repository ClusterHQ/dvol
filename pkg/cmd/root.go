package cmd

import (
	"fmt"
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

var basePath string
var disableDockerIntegration bool

var dvolAPIOptions api.DvolAPIOptions

var RootCmd = &cobra.Command{
	Use:   "dvol",
	Short: "dvol is a version control system for your development data in Docker",
	Long: `dvol
====
dvol lets you commit, reset and branch the containerized databases
running on your laptop so you can easily save a particular state
and come back to it later.`,
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		// Make the basePath directory if it does not exist
		if _, err := os.Stat(basePath); err != nil {
			if err := os.MkdirAll(basePath, 0600); err != nil {
				return fmt.Errorf("Could not create dvol directory %s: %v", basePath, err)
			}
		}

		dvolAPIOptions = api.DvolAPIOptions{
			BasePath:                 basePath,
			DisableDockerIntegration: disableDockerIntegration,
		}

		return initialiseConfig()
	},
}

func init() {
	RootCmd.AddCommand(NewCmdBranch(os.Stdout))
	RootCmd.AddCommand(NewCmdCheckout(os.Stdout))
	RootCmd.AddCommand(NewCmdConfig(os.Stdout))
	RootCmd.AddCommand(NewCmdCommit(os.Stdout))
	RootCmd.AddCommand(NewCmdInit(os.Stdout))
	RootCmd.AddCommand(NewCmdList(os.Stdout))
	RootCmd.AddCommand(NewCmdLog(os.Stdout))
	RootCmd.AddCommand(NewCmdReset(os.Stdout))
	RootCmd.AddCommand(NewCmdRm(os.Stdout))
	RootCmd.AddCommand(NewCmdSwitch(os.Stdout))

	RootCmd.PersistentFlags().StringVarP(&basePath, "path", "p", "/var/lib/dvol/volumes",
		"The name of the directory to use")
	RootCmd.PersistentFlags().BoolVar(&disableDockerIntegration,
		"disable-docker-integration", false, "Do not attempt to list/stop/start"+
			" docker containers which are using dvol volumes")
}
