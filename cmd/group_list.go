package cmd

import (
	"strings"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var groupListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all groups",
	Long:  `List all entity groups.`,
	RunE:  runGroupList,
}

func init() {
	groupCmd.AddCommand(groupListCmd)
}

func runGroupList(cmd *cobra.Command, args []string) error {
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

	states, err := ws.GetStates()
	if err != nil {
		return err
	}

	var result []map[string]interface{}
	for _, s := range states {
		state, ok := s.(map[string]interface{})
		if !ok {
			continue
		}

		entityID, _ := state["entity_id"].(string)
		if !strings.HasPrefix(entityID, "group.") {
			continue
		}

		attrs, _ := state["attributes"].(map[string]interface{})
		result = append(result, map[string]interface{}{
			"entity_id":   entityID,
			"name":        attrs["friendly_name"],
			"entity_list": attrs["entity_id"],
		})
	}

	client.PrintOutput(result, textMode, "")
	return nil
}
