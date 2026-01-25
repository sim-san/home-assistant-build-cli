package cmd

import (
	"github.com/spf13/cobra"
)

var automationCmd = &cobra.Command{
	Use:   "automation",
	Short: "Manage Home Assistant automations",
	Long:  `Create, update, delete, and trigger automations.`,
}

func init() {
	rootCmd.AddCommand(automationCmd)
}
