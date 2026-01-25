package cmd

import (
	"github.com/spf13/cobra"
)

var groupCmd = &cobra.Command{
	Use:   "group",
	Short: "Manage entity groups",
	Long:  `Create, update, and delete entity groups.`,
}

func init() {
	rootCmd.AddCommand(groupCmd)
}
