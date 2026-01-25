package cmd

import (
	"fmt"
	"os"
	"path"
	"strings"

	"github.com/home-assistant/hab/config"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	cfgDir   string
	textMode bool
	verbose  bool
)

// ExitWithError signals that the program should exit with a non-zero code
var ExitWithError = false

var rootCmd = &cobra.Command{
	Use:   path.Base(os.Args[0]),
	Short: "Home Assistant Builder - Build Home Assistant configurations",
	Long: `Home Assistant Builder (hab) is a CLI utility designed for LLMs
to build and manage Home Assistant configurations.

Output is JSON by default for easy parsing. Use --text for human-readable output.`,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		// Set log level based on verbose flag
		if viper.GetBool("verbose") {
			log.SetLevel(log.DebugLevel)
		} else {
			log.SetLevel(log.WarnLevel)
		}

		log.WithFields(log.Fields{
			"url":     viper.GetString("url"),
			"text":    viper.GetBool("text"),
			"verbose": viper.GetBool("verbose"),
			"config":  viper.GetString("config"),
		}).Debug("Configuration")
	},
}

// Execute runs the root command
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		ExitWithError = true
	}
}

func init() {
	cobra.OnInitialize(initConfig)

	// Global flags
	rootCmd.PersistentFlags().StringVar(&cfgDir, "config", "", "Path to config directory (default: ~/.config/home-assistant-builder)")
	rootCmd.PersistentFlags().BoolVar(&textMode, "text", false, "Use human-readable text output instead of JSON")
	rootCmd.PersistentFlags().BoolVar(&verbose, "verbose", false, "Show verbose output")

	// Bind flags to viper
	viper.BindPFlag("config", rootCmd.PersistentFlags().Lookup("config"))
	viper.BindPFlag("text", rootCmd.PersistentFlags().Lookup("text"))
	viper.BindPFlag("verbose", rootCmd.PersistentFlags().Lookup("verbose"))

	// Shell completions
	rootCmd.RegisterFlagCompletionFunc("text", boolCompletions)
	rootCmd.RegisterFlagCompletionFunc("verbose", boolCompletions)
	rootCmd.MarkPersistentFlagDirname("config")
}

func initConfig() {
	// Set environment variable prefix
	viper.SetEnvPrefix("HAB")
	viper.SetEnvKeyReplacer(strings.NewReplacer("-", "_"))
	viper.AutomaticEnv()

	// Bind specific environment variables
	viper.BindEnv("url", "HAB_URL")
	viper.BindEnv("token", "HAB_TOKEN")
	viper.BindEnv("refresh-token", "HAB_REFRESH_TOKEN")

	// Set defaults
	config.InitDefaults()

	// Read config file if it exists
	if cfgDir != "" {
		viper.SetConfigFile(config.GetConfigPath(cfgDir))
	} else {
		configDir := config.GetConfigDir("")
		viper.AddConfigPath(configDir)
		viper.SetConfigName("config")
		viper.SetConfigType("json")
	}

	// Read config file (ignore errors if not found)
	if err := viper.ReadInConfig(); err == nil {
		log.WithField("configfile", viper.ConfigFileUsed()).Debug("Using config file")
	}
}

func boolCompletions(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
	return []string{"true", "false"}, cobra.ShellCompDirectiveNoFileComp
}
