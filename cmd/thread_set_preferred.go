package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var threadSetPreferredCmd = &cobra.Command{
	Use:   "set-preferred <dataset_id>",
	Short: "Set a dataset as the preferred network",
	Long:  `Set a Thread dataset as the preferred network.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runThreadSetPreferred,
}

func init() {
	threadCmd.AddCommand(threadSetPreferredCmd)
}

func runThreadSetPreferred(cmd *cobra.Command, args []string) error {
	datasetID := args[0]
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

	_, err = ws.SendCommand("thread/set_preferred_dataset", map[string]interface{}{
		"dataset_id": datasetID,
	})
	if err != nil {
		return err
	}

	client.PrintSuccess(nil, textMode, fmt.Sprintf("Thread dataset %s set as preferred.", datasetID))
	return nil
}
