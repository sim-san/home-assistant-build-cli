package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	areaCreateFloor string
	areaCreateIcon  string
)

var areaCreateCmd = &cobra.Command{
	Use:   "create <name>",
	Short: "Create a new area",
	Long:  `Create a new area in Home Assistant.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runAreaCreate,
}

func init() {
	areaCmd.AddCommand(areaCreateCmd)
	areaCreateCmd.Flags().StringVar(&areaCreateFloor, "floor", "", "Floor ID to assign")
	areaCreateCmd.Flags().StringVar(&areaCreateIcon, "icon", "", "Icon for the area")
}

func runAreaCreate(cmd *cobra.Command, args []string) error {
	name := args[0]
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

	params := make(map[string]interface{})
	if areaCreateFloor != "" {
		params["floor_id"] = areaCreateFloor
	}
	if areaCreateIcon != "" {
		params["icon"] = areaCreateIcon
	}

	result, err := ws.AreaRegistryCreate(name, params)
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, fmt.Sprintf("Area '%s' created.", name))
	return nil
}
