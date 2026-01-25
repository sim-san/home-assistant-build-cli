package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var labelAssignCmd = &cobra.Command{
	Use:   "assign <label_id> <entity_id>",
	Short: "Assign label to entity",
	Long:  `Assign a label to an entity.`,
	Args:  cobra.ExactArgs(2),
	RunE:  runLabelAssign,
}

func init() {
	labelCmd.AddCommand(labelAssignCmd)
}

func runLabelAssign(cmd *cobra.Command, args []string) error {
	labelID := args[0]
	entityID := args[1]
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

	// First get current entity labels
	entity, err := ws.EntityRegistryGet(entityID)
	if err != nil {
		return err
	}

	currentLabels, _ := entity["labels"].([]interface{})
	labels := make([]string, 0, len(currentLabels)+1)
	for _, l := range currentLabels {
		if ls, ok := l.(string); ok {
			if ls == labelID {
				// Already has label
				client.PrintSuccess(nil, textMode, fmt.Sprintf("Entity %s already has label %s.", entityID, labelID))
				return nil
			}
			labels = append(labels, ls)
		}
	}
	labels = append(labels, labelID)

	// Update entity with new labels
	result, err := ws.EntityRegistryUpdate(entityID, map[string]interface{}{
		"labels": labels,
	})
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, fmt.Sprintf("Label %s assigned to %s.", labelID, entityID))
	return nil
}
