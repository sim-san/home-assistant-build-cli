package cmd

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var areaDeleteForce bool

var areaDeleteCmd = &cobra.Command{
	Use:   "delete <area_id>",
	Short: "Delete an area",
	Long:  `Delete an area from Home Assistant.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runAreaDelete,
}

func init() {
	areaCmd.AddCommand(areaDeleteCmd)
	areaDeleteCmd.Flags().BoolVarP(&areaDeleteForce, "force", "f", false, "Skip confirmation")
}

func runAreaDelete(cmd *cobra.Command, args []string) error {
	areaID := args[0]
	configDir := viper.GetString("config")
	textMode := viper.GetBool("text")

	if !areaDeleteForce && !textMode {
		fmt.Printf("Delete area %s? [y/N]: ", areaID)
		reader := bufio.NewReader(os.Stdin)
		response, _ := reader.ReadString('\n')
		response = strings.ToLower(strings.TrimSpace(response))
		if response != "y" && response != "yes" {
			fmt.Println("Cancelled.")
			return nil
		}
	}

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

	if err := ws.AreaRegistryDelete(areaID); err != nil {
		return err
	}

	client.PrintSuccess(nil, textMode, fmt.Sprintf("Area '%s' deleted.", areaID))
	return nil
}
