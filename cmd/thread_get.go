package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var threadGetCmd = &cobra.Command{
	Use:   "get <dataset_id>",
	Short: "Get dataset details including TLV",
	Long:  `Get full details of a Thread dataset.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runThreadGet,
}

func init() {
	threadCmd.AddCommand(threadGetCmd)
}

func runThreadGet(cmd *cobra.Command, args []string) error {
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

	result, err := ws.SendCommand("thread/get_dataset_tlv", map[string]interface{}{
		"dataset_id": datasetID,
	})
	if err != nil {
		return err
	}

	client.PrintOutput(result, textMode, "")
	return nil
}
