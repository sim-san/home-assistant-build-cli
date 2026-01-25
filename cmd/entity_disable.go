package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var entityDisableCmd = &cobra.Command{
	Use:   "disable <entity_id>",
	Short: "Disable an entity",
	Long:  `Disable an entity so it is no longer active.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runEntityDisable,
}

func init() {
	entityCmd.AddCommand(entityDisableCmd)
}

func runEntityDisable(cmd *cobra.Command, args []string) error {
	entityID := args[0]
	configDir := viper.GetString("config")
	textMode := viper.GetBool("text")

	manager := auth.NewManager(configDir)
	creds, err := manager.GetCredentials()
	if err != nil || creds == nil {
		return err
	}

	ws := client.NewWebSocketClient(creds.URL, creds.AccessToken)
	if err := ws.Connect(); err != nil {
		return err
	}
	defer ws.Close()

	result, err := ws.EntityRegistryUpdate(entityID, map[string]interface{}{
		"disabled_by": "user",
	})
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, fmt.Sprintf("Entity %s disabled.", entityID))
	return nil
}
