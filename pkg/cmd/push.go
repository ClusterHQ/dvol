package cmd

import (
	"io"
	"github.com/spf13/cobra"
)

func NewCmdPush(out io.Writer) *cobra.Command {
	return &cobra.Command{
		Use: "push",
		Short: "Push a volume to Volume Hub",
		Run: func(cmd *cobra.Command, args []string) {
		},
	}
}
