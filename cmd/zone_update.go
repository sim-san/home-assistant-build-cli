package cmd

import (
	"fmt"

	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	zoneUpdateName      string
	zoneUpdateLatitude  float64
	zoneUpdateLongitude float64
	zoneUpdateRadius    float64
	zoneUpdateIcon      string
	zoneUpdatePassive   bool
)

var zoneUpdateCmd = &cobra.Command{
	Use:   "update <zone_id>",
	Short: "Update a zone",
	Long:  `Update an existing zone.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runZoneUpdate,
}

func init() {
	zoneCmd.AddCommand(zoneUpdateCmd)
	zoneUpdateCmd.Flags().StringVar(&zoneUpdateName, "name", "", "New name for the zone")
	zoneUpdateCmd.Flags().Float64Var(&zoneUpdateLatitude, "latitude", 0, "New latitude")
	zoneUpdateCmd.Flags().Float64Var(&zoneUpdateLongitude, "longitude", 0, "New longitude")
	zoneUpdateCmd.Flags().Float64Var(&zoneUpdateRadius, "radius", 0, "New radius in meters")
	zoneUpdateCmd.Flags().StringVar(&zoneUpdateIcon, "icon", "", "New icon")
	zoneUpdateCmd.Flags().BoolVar(&zoneUpdatePassive, "passive", false, "Set passive mode")
}

func runZoneUpdate(cmd *cobra.Command, args []string) error {
	zoneID := args[0]
	configDir := viper.GetString("config")
	textMode := viper.GetBool("text")

	params := make(map[string]interface{})
	if zoneUpdateName != "" {
		params["name"] = zoneUpdateName
	}
	if cmd.Flags().Changed("latitude") {
		params["latitude"] = zoneUpdateLatitude
	}
	if cmd.Flags().Changed("longitude") {
		params["longitude"] = zoneUpdateLongitude
	}
	if cmd.Flags().Changed("radius") {
		params["radius"] = zoneUpdateRadius
	}
	if zoneUpdateIcon != "" {
		params["icon"] = zoneUpdateIcon
	}
	if cmd.Flags().Changed("passive") {
		params["passive"] = zoneUpdatePassive
	}

	if len(params) == 0 {
		return fmt.Errorf("no update parameters provided")
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

	result, err := ws.ZoneUpdate(zoneID, params)
	if err != nil {
		return err
	}

	client.PrintSuccess(result, textMode, fmt.Sprintf("Zone '%s' updated.", zoneID))
	return nil
}
