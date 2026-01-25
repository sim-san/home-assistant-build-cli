package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var dashboardListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all dashboards",
	Long:  `List all dashboards in Home Assistant.`,
	RunE:  runDashboardList,
}

func init() {
	dashboardCmd.AddCommand(dashboardListCmd)
}

func runDashboardList(cmd *cobra.Command, args []string) error {
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

	result, err := ws.SendCommand("lovelace/dashboards/list", nil)
	if err != nil {
		return err
	}

	client.PrintOutput(result, textMode, "")
	return nil
}
