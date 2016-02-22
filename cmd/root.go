package cmd
import (
    "fmt"
    "github.com/spf13/cobra"
)

var RootCmd = &cobra.Command {
    Use: "dvol",
    Short: "dvol is a version control system for your development data in Docker",
    Long: `dvol lets you commit, reset and branch the containerized databases
running on your laptop so you can easily save a particular state
and come back to it later.`,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Hello, world! I am really here.", args)
    },
}

func init() {
    // cobra.OnInitialize(initConfig)
    // TODO support: dvol -p <custom_path> init <volume_name>
    var path string
    // XXX "p" is the default, not the short version
    RootCmd.PersistentFlags().StringVarP(&path, "path", "p", "/var/lib/dvol/volumes",
        "The name of the directory to use")
}
