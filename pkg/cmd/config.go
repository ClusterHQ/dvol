package cmd

import (
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"path"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"gopkg.in/yaml.v2"
)

var listAll bool

type Config struct {
	// Used to marshal the configuration into YAML
	UserName  string `mapstructure:"user.name" yaml:"user.name"`
	UserEmail string `mapstructure:"user.email" yaml:"user.email"`
}

func isValidKey(key string) bool {
	switch key {
	case
		"user.name",
		"user.email":
		return true
	}
	return false
}

func NewCmdConfig(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "config name [value]",
		Short: "Get or set global options",
		RunE: func(cmd *cobra.Command, args []string) error {
			return dispatchConfig(args, os.Stdout)
		},
	}
	cmd.Flags().BoolVarP(&listAll, "list", "l", false, "List all")
	return cmd
}

func initialiseConfig() error {
	viper.SetConfigFile(configPath())
	if err := viper.ReadInConfig(); err != nil {
		if !os.IsNotExist(err) {
			return err
		}
	}
	return nil
}

func configPath() string {
	// Return the configuration file path
	return path.Join(basePath, "config.yml")
}

func dispatchConfig(args []string, out io.Writer) error {
	if len(args) == 0 {
		if listAll {
			return listAllConfig(out)
		} else {
			return errors.New("No operation specified")
		}
	} else if len(args) == 1 {
		return getConfigValue(args[0], out)
	} else if len(args) == 2 {
		return setConfigValue(args[0], args[1])
	} else {
		return errors.New("Too many arguments")
	}
}

func getConfigValue(key string, out io.Writer) error {
	if !isValidKey(key) {
		return fmt.Errorf("'%s' is not a valid configuration key", key)
	}

	value := viper.GetString(key)
	if len(value) > 0 {
		value += "\n"
	}
	_, err := io.WriteString(out, value)
	return err
}

func setConfigValue(key, value string) error {
	if !isValidKey(key) {
		return fmt.Errorf("'%s' is not a valid configuration key", key)
	}

	viper.Set(key, value)
	return saveConfig()
}

func listAllConfig(out io.Writer) error {
	config, err := unmarshalConfig()
	if err != nil {
		return nil
	}

	// Iterating over structs is hard and there are only two configuration
	// directives at time of writing. Hard-code the output format for now, and
	// invest in a more maintainable method in the future.
	_, err = fmt.Fprintf(out, "user.name=%s\nuser.email=%s\n",
		config.UserName, config.UserEmail)
	return err
}

func unmarshalConfig() (Config, error) {
	var C Config
	err := viper.Unmarshal(&C)
	return C, err
}

func saveConfig() error {
	config, err := unmarshalConfig()
	if err != nil {
		return err
	}
	yamlConfig, err := yaml.Marshal(config)
	if err != nil {
		return err
	}

	configPath := configPath()
	file, err := ioutil.TempFile(basePath, "dvol_config")
	if err != nil {
		return err
	}
	if err := os.Chmod(file.Name(), 0600); err != nil {
		return err
	}
	if _, err := file.Write(yamlConfig); err != nil {
		os.Remove(file.Name())
		return err
	}
	return os.Rename(file.Name(), configPath)
}
