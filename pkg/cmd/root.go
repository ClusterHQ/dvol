package cmd

import (
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
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
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		dvolAPIOptions = api.DvolAPIOptions{
			BasePath:                 basePath,
			DisableDockerIntegration: disableDockerIntegration,
		}
	},
}

func init() {
	// cobra.OnInitialize(initConfig)
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

	viper.SetConfigName("config")
	viper.AddConfigPath("$HOME/.dvol")
	viper.ReadInConfig()
}
