package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var entityGetCmd = &cobra.Command{
	Use:   "get <entity_id>",
	Short: "Get entity state and attributes",
	Long:  `Get the current state and attributes of an entity.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runEntityGet,
}

func init() {
	entityCmd.AddCommand(entityGetCmd)
}

func runEntityGet(cmd *cobra.Command, args []string) error {
	entityID := args[0]
	configDir := viper.GetString("config")
	textMode := viper.GetBool("text")

	manager := auth.NewManager(configDir)
	restClient, err := manager.GetRestClient()
	if err != nil {
		return err
	}

	state, err := restClient.GetState(entityID)
	if err != nil {
		return err
	}

	client.PrintOutput(state, textMode, "")
	return nil
}
