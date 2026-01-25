package cmd

import (
	"strings"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var helperListCmd = &cobra.Command{
	Use:   "list [type]",
	Short: "List helper entities",
	Long:  `List all helper entities, optionally filtered by type.`,
	Args:  cobra.MaximumNArgs(1),
	RunE:  runHelperList,
}

func init() {
	helperCmd.AddCommand(helperListCmd)
}

func runHelperList(cmd *cobra.Command, args []string) error {
	var filterType string
	if len(args) > 0 {
		filterType = args[0]
	}

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

	// Helper domains
	helperDomains := map[string]bool{
		"input_boolean":  true,
		"input_number":   true,
		"input_text":     true,
		"input_select":   true,
		"input_datetime": true,
		"input_button":   true,
		"counter":        true,
		"timer":          true,
		"schedule":       true,
	}

	var result []map[string]interface{}
	for _, e := range entities {
		entity, ok := e.(map[string]interface{})
		if !ok {
			continue
		}

		entityID, _ := entity["entity_id"].(string)
		parts := strings.SplitN(entityID, ".", 2)
		if len(parts) < 2 {
			continue
		}

		domain := parts[0]
		if !helperDomains[domain] {
			continue
		}

		if filterType != "" && domain != filterType && domain != "input_"+filterType {
			continue
		}

		result = append(result, map[string]interface{}{
			"entity_id": entityID,
			"name":      entity["name"],
			"type":      domain,
		})
	}

	client.PrintOutput(result, textMode, "")
	return nil
}
