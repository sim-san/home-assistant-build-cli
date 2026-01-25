package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var authLogoutCmd = &cobra.Command{
	Use:   "logout",
	Short: "Remove stored credentials",
	Long:  `Remove stored credentials from the local machine.`,
	RunE:  runAuthLogout,
}

func init() {
	authCmd.AddCommand(authLogoutCmd)
}

func runAuthLogout(cmd *cobra.Command, args []string) error {
	configDir := viper.GetString("config")
	textMode := viper.GetBool("text")
	manager := auth.NewManager(configDir)

	if manager.Logout() {
		client.PrintSuccess(nil, textMode, "Successfully logged out.")
	} else {
		client.PrintSuccess(nil, textMode, "No credentials to remove.")
	}

	return nil
}
