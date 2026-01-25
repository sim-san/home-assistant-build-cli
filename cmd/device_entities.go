package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var deviceEntitiesCmd = &cobra.Command{
	Use:   "entities <device_id>",
	Short: "List entities for a device",
	Long:  `List all entities that belong to a device.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runDeviceEntities,
}

func init() {
	deviceCmd.AddCommand(deviceEntitiesCmd)
}

func runDeviceEntities(cmd *cobra.Command, args []string) error {
	deviceID := args[0]
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

	entities, err := ws.EntityRegistryList()
	if err != nil {
		return err
	}

	var result []map[string]interface{}
	for _, e := range entities {
		entity, ok := e.(map[string]interface{})
		if !ok {
			continue
		}
		if entity["device_id"] == deviceID {
			result = append(result, map[string]interface{}{
				"entity_id": entity["entity_id"],
				"name":      entity["name"],
				"disabled":  entity["disabled_by"] != nil,
			})
		}
	}

	client.PrintOutput(result, textMode, "")
	return nil
}
