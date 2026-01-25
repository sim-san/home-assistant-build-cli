package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var backupListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available backups",
	Long:  `List all available backups.`,
	RunE:  runBackupList,
}

func init() {
	backupCmd.AddCommand(backupListCmd)
}

func runBackupList(cmd *cobra.Command, args []string) error {
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

	result, err := ws.SendCommand("backup/info", nil)
	if err != nil {
		return err
	}

	if resultMap, ok := result.(map[string]interface{}); ok {
		if backups, ok := resultMap["backups"]; ok {
			client.PrintOutput(backups, textMode, "")
			return nil
		}
	}

	client.PrintOutput(result, textMode, "")
	return nil
}
