package cmd

import (
	"github.com/spf13/cobra"
)

var authCmd = &cobra.Command{
	Use:   "auth",
	Short: "Authentication management",
	Long:  `Manage authentication with Home Assistant.`,
}

func init() {
	rootCmd.AddCommand(authCmd)
}
