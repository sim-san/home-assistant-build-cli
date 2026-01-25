package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var labelListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all labels",
	Long:  `List all labels in Home Assistant.`,
	RunE:  runLabelList,
}

func init() {
	labelCmd.AddCommand(labelListCmd)
}

func runLabelList(cmd *cobra.Command, args []string) error {
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

	labels, err := ws.LabelRegistryList()
	if err != nil {
		return err
	}

	client.PrintOutput(labels, textMode, "")
	return nil
}
