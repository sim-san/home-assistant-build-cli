package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var blueprintImportCmd = &cobra.Command{
	Use:   "import <url>",
	Short: "Import a blueprint from URL",
	Long:  `Import a blueprint from a URL.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runBlueprintImport,
}

func init() {
	blueprintCmd.AddCommand(blueprintImportCmd)
}

func runBlueprintImport(cmd *cobra.Command, args []string) error {
	url := args[0]
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

	result, err := ws.SendCommand("blueprint/import", map[string]interface{}{
		"url": url,
	})
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, fmt.Sprintf("Blueprint imported from %s", url))
	return nil
}
