package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var zoneListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all zones",
	Long:  `List all zones in Home Assistant.`,
	RunE:  runZoneList,
}

func init() {
	zoneCmd.AddCommand(zoneListCmd)
}

func runZoneList(cmd *cobra.Command, args []string) error {
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

	zones, err := ws.ZoneList()
	if err != nil {
		return err
	}

	client.PrintOutput(zones, textMode, "")
	return nil
}
