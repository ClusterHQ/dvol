package cmd

import (
	"io"
	"github.com/spf13/cobra"
)

func NewCmdClone(out io.Writer) *cobra.Command {
	return &cobra.Command{
		Use: "clone",
		Short: "Clone a volume from Volume Hub",
		Run: func(cmd *cobra.Command, args []string) {
		},
	}
}
