package main

import (
	"os"

	"github.com/home-assistant/hab/cmd"
)

func main() {
	cmd.Execute()
	if cmd.ExitWithError {
		os.Exit(1)
	}
}
