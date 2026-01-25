package cmd

import (
	"github.com/spf13/cobra"
)

var helperCmd = &cobra.Command{
	Use:   "helper",
	Short: "Manage helper entities",
	Long:  `Create, update, and delete helper entities.`,
}

func init() {
	rootCmd.AddCommand(helperCmd)
}
