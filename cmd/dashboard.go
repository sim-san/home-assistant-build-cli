package cmd

import (
	"github.com/spf13/cobra"
)

var dashboardCmd = &cobra.Command{
	Use:   "dashboard",
	Short: "Manage dashboards",
	Long:  `Create, update, and delete dashboards.`,
}

func init() {
	rootCmd.AddCommand(dashboardCmd)
}
