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

type Config struct {
	// Used to marshal the configuration into YAML
	UserName string `mapstructure:"user.name" yaml:"user.name"`
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
	return cmd
}

func dispatchConfig(args []string, out io.Writer) error {
	if len(args) == 0 {
		return errors.New("Not enough arguments")
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
	if _, err := io.WriteString(out, value); err != nil { 
		return err
	}
	return nil
}
func setConfigValue(key, value string) error {
	if !isValidKey(key) {
		return fmt.Errorf("'%s' is not a valid configuration key", key)
	}

	viper.Set(key, value)
	return saveConfig()
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

	configPath := path.Join(basePath, "config.yml")
	file, err := ioutil.TempFile(basePath, "dvol_config")
	if err != nil {
		return err
	}
	os.Chmod(file.Name(), 0600)
	if _, err := file.Write(yamlConfig); err != nil {
		os.Remove(file.Name())
		return err
	}
	return os.Rename(file.Name(), configPath)
}
