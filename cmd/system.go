package cmd

import (
	"github.com/spf13/cobra"
)

var systemCmd = &cobra.Command{
	Use:   "system",
	Short: "System operations",
	Long:  `View system info, check config, restart, and more.`,
}

func init() {
	rootCmd.AddCommand(systemCmd)
}
