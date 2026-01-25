package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var backupCreateCmd = &cobra.Command{
	Use:   "create [name]",
	Short: "Create a new backup",
	Long:  `Create a new backup of Home Assistant.`,
	Args:  cobra.MaximumNArgs(1),
	RunE:  runBackupCreate,
}

func init() {
	backupCmd.AddCommand(backupCreateCmd)
}

func runBackupCreate(cmd *cobra.Command, args []string) error {
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

	params := map[string]interface{}{}
	if len(args) > 0 {
		params["name"] = args[0]
	}

	result, err := ws.SendCommand("backup/generate", params)
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, "Backup creation initiated.")
	return nil
}
