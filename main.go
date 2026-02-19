package main

import (
	"os"

	"github.com/sim-san/home-assistant-build-cli/cmd"
)

// version is set at build time via ldflags
var version = "dev"

func main() {
	cmd.Version = version
	cmd.Execute()
	if cmd.ExitWithError {
		os.Exit(1)
	}
}
