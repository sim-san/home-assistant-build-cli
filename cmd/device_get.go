package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var deviceGetCmd = &cobra.Command{
	Use:   "get <device_id>",
	Short: "Get device details",
	Long:  `Get detailed information about a device.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runDeviceGet,
}

func init() {
	deviceCmd.AddCommand(deviceGetCmd)
}

func runDeviceGet(cmd *cobra.Command, args []string) error {
	deviceID := args[0]
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

	devices, err := ws.DeviceRegistryList()
	if err != nil {
		return err
	}

	for _, d := range devices {
		device, ok := d.(map[string]interface{})
		if !ok {
			continue
		}
		if device["id"] == deviceID {
			client.PrintOutput(device, textMode, "")
			return nil
		}
	}

	return fmt.Errorf("device '%s' not found", deviceID)
}
