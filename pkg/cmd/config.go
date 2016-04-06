package cmd

import (
	"errors"
	"io"
	"os"

	"github.com/spf13/cobra"
	//"github.com/spf13/viper"
)

func NewCmdConfig(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:	"config name [value]",
		Short:	"Get or set global options",
		RunE: func(cmd *cobra.Command, args []string) error {
			return dispatchConfig(args, os.Stdout)
		},
	}
	return cmd
}

func dispatchConfig(args []string, out io.Writer) error {
	if len(args) == 1 {
		return errors.New("Any operation other than setting a value is not implemented yet.")
	} else if len(args) == 2 {
		return setConfigValue(args[0], args[1], out)
	} else {
		return errors.New("Too many arguments")
	}
}

func setConfigValue(key, value string, out io.Writer) error {
	return nil
}
