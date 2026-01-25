package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var threadListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all Thread datasets",
	Long:  `List all Thread network datasets.`,
	RunE:  runThreadList,
}

func init() {
	threadCmd.AddCommand(threadListCmd)
}

func runThreadList(cmd *cobra.Command, args []string) error {
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

	result, err := ws.SendCommand("thread/list_datasets", nil)
	if err != nil {
		return err
	}

	client.PrintOutput(result, textMode, "")
	return nil
}
