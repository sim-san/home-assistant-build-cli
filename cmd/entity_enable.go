package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var entityEnableCmd = &cobra.Command{
	Use:   "enable <entity_id>",
	Short: "Enable a disabled entity",
	Long:  `Enable an entity that was previously disabled.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runEntityEnable,
}

func init() {
	entityCmd.AddCommand(entityEnableCmd)
}

func runEntityEnable(cmd *cobra.Command, args []string) error {
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
		"disabled_by": nil,
	})
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, fmt.Sprintf("Entity %s enabled.", entityID))
	return nil
}
