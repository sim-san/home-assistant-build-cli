package cmd

import (
	"github.com/home-assistant/hab/auth"
	"github.com/home-assistant/hab/client"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	calendarListStart string
	calendarListEnd   string
)

var calendarListCmd = &cobra.Command{
	Use:   "list <entity_id>",
	Short: "List calendar events",
	Long:  `List events from a calendar entity.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runCalendarList,
}

func init() {
	calendarCmd.AddCommand(calendarListCmd)
	calendarListCmd.Flags().StringVarP(&calendarListStart, "start", "s", "", "Start time (ISO format)")
	calendarListCmd.Flags().StringVarP(&calendarListEnd, "end", "e", "", "End time (ISO format)")
}

func runCalendarList(cmd *cobra.Command, args []string) error {
	entityID := args[0]
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
		"entity_id": entityID,
	}
	if calendarListStart != "" {
		params["start"] = calendarListStart
	}
	if calendarListEnd != "" {
		params["end"] = calendarListEnd
	}

	result, err := ws.SendCommand("calendar/event/list", params)
	if err != nil {
		return err
	}

	client.PrintOutput(result, textMode, "")
	return nil
}
