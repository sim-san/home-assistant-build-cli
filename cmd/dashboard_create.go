package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	dashboardCreateTitle         string
	dashboardCreateIcon          string
	dashboardCreateShowInSidebar bool
	dashboardCreateRequireAdmin  bool
)

var dashboardCreateCmd = &cobra.Command{
	Use:   "create <url_path>",
	Short: "Create a new dashboard",
	Long:  `Create a new storage-mode dashboard.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runDashboardCreate,
}

func init() {
	dashboardCmd.AddCommand(dashboardCreateCmd)
	dashboardCreateCmd.Flags().StringVar(&dashboardCreateTitle, "title", "", "Dashboard title (required)")
	dashboardCreateCmd.Flags().StringVar(&dashboardCreateIcon, "icon", "", "Dashboard icon (e.g., mdi:home)")
	dashboardCreateCmd.Flags().BoolVar(&dashboardCreateShowInSidebar, "sidebar", true, "Show in sidebar")
	dashboardCreateCmd.Flags().BoolVar(&dashboardCreateRequireAdmin, "require-admin", false, "Require admin access")
	dashboardCreateCmd.MarkFlagRequired("title")
}

func runDashboardCreate(cmd *cobra.Command, args []string) error {
	urlPath := args[0]
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

	params := map[string]interface{}{
		"url_path":        urlPath,
		"mode":            "storage",
		"title":           dashboardCreateTitle,
		"show_in_sidebar": dashboardCreateShowInSidebar,
		"require_admin":   dashboardCreateRequireAdmin,
	}
	if dashboardCreateIcon != "" {
		params["icon"] = dashboardCreateIcon
	}

	result, err := ws.SendCommand("lovelace/dashboards/create", params)
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, fmt.Sprintf("Dashboard %s created successfully.", urlPath))
	return nil
}
