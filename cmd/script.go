package cmd

import (
	"github.com/spf13/cobra"
)

var scriptCmd = &cobra.Command{
	Use:   "script",
	Short: "Manage scripts",
	Long:  `Create, update, delete, and run scripts.`,
}

func init() {
	rootCmd.AddCommand(scriptCmd)
}
