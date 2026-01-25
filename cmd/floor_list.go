package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var floorListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all floors",
	Long:  `List all floors in Home Assistant.`,
	RunE:  runFloorList,
}

func init() {
	floorCmd.AddCommand(floorListCmd)
}

func runFloorList(cmd *cobra.Command, args []string) error {
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

	floors, err := ws.FloorRegistryList()
	if err != nil {
		return err
	}

	client.PrintOutput(floors, textMode, "")
	return nil
}
