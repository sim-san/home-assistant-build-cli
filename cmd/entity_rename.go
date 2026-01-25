package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var entityRenameCmd = &cobra.Command{
	Use:   "rename <entity_id> <new_name>",
	Short: "Rename an entity",
	Long:  `Rename an entity by setting its friendly name.`,
	Args:  cobra.ExactArgs(2),
	RunE:  runEntityRename,
}

func init() {
	entityCmd.AddCommand(entityRenameCmd)
}

func runEntityRename(cmd *cobra.Command, args []string) error {
	entityID := args[0]
	newName := args[1]
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
		"name": newName,
	})
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, fmt.Sprintf("Entity renamed to %s.", newName))
	return nil
}
