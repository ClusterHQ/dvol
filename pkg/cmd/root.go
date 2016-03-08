package cmd

import (
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

var dvol *api.DvolAPI
var disableDockerIntegration bool

const DEFAULT_BRANCH string = "master"

var RootCmd = &cobra.Command{
	Use:   "dvol",
	Short: "dvol is a version control system for your development data in Docker",
	Long: `dvol
====
dvol lets you commit, reset and branch the containerized databases
running on your laptop so you can easily save a particular state
and come back to it later.`,
}

func init() {
	// cobra.OnInitialize(initConfig)
	// TODO support: dvol -p <custom_path> init <volume_name>
	RootCmd.AddCommand(NewCmdInit(os.Stdout))
	RootCmd.AddCommand(NewCmdRm(os.Stdout))
	RootCmd.AddCommand(NewCmdSwitch(os.Stdout))
	RootCmd.AddCommand(NewCmdCheckout(os.Stdout))

	var basePath string
	RootCmd.PersistentFlags().StringVarP(&basePath, "path", "p", "/var/lib/dvol/volumes",
		"The name of the directory to use")
	dvol = api.NewDvolAPI(basePath)
	RootCmd.PersistentFlags().BoolVar(&disableDockerIntegration,
		"disable-docker-integration", false, "Do not attempt to list/stop/start"+
			" docker containers which are using dvol volumes")
}
