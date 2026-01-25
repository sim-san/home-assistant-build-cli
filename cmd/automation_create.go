package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/home-assistant/hab/input"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	automationCreateData   string
	automationCreateFile   string
	automationCreateFormat string
)

var automationCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new automation",
	Long:  `Create a new automation from JSON or YAML.`,
	RunE:  runAutomationCreate,
}

func init() {
	automationCmd.AddCommand(automationCreateCmd)
	automationCreateCmd.Flags().StringVarP(&automationCreateData, "data", "d", "", "Automation configuration as JSON")
	automationCreateCmd.Flags().StringVarP(&automationCreateFile, "file", "f", "", "Path to config file")
	automationCreateCmd.Flags().StringVar(&automationCreateFormat, "format", "", "Input format (json, yaml)")
}

func runAutomationCreate(cmd *cobra.Command, args []string) error {
	configDir := viper.GetString("config")
	textMode := viper.GetBool("text")

	config, err := input.ParseInput(automationCreateData, automationCreateFile, automationCreateFormat)
	if err != nil {
		return err
	}

	if _, ok := config["alias"]; !ok {
		return fmt.Errorf("automation must have an 'alias' field")
	}

	manager := auth.NewManager(configDir)
	restClient, err := manager.GetRestClient()
	if err != nil {
		return err
	}

	result, err := restClient.Post("config/automation/config", config)
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, "Automation created successfully.")
	return nil
}
