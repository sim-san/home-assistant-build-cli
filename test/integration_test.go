package test

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

const (
	// EmptyHassToken is the long-lived access token from empty-hass
	EmptyHassToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIyZWZkZGJjZmY0MzQ0NGRlYmUyMDhkNDUyM2RlNTIwMSIsImlhdCI6MTc2OTI4MjkyNiwiZXhwIjoyMDg0NjQyOTI2fQ.ZYSmLdcv5EfGCXrwO2Nd6bxHrxxU-7ieuE0ySwurU9A"
	// EmptyHassURL is the default URL for empty-hass
	EmptyHassURL = "http://localhost:8123"
)

// TestIntegration runs integration tests against empty-hass
func TestIntegration(t *testing.T) {
	// Skip if not running integration tests
	if os.Getenv("INTEGRATION_TEST") == "" {
		t.Skip("Skipping integration test. Set INTEGRATION_TEST=1 to run.")
	}

	// Build the CLI first
	habPath := buildCLI(t)
	defer os.Remove(habPath)

	// Start empty-hass
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	emptyHass := startEmptyHass(ctx, t)
	defer func() {
		cancel()
		emptyHass.Wait()
	}()

	// Wait for empty-hass to be ready
	waitForEmptyHass(t)

	// Create a temp config directory for tests
	configDir, err := os.MkdirTemp("", "hab-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp config dir: %v", err)
	}
	defer os.RemoveAll(configDir)

	// Run test cases
	t.Run("AuthLogin", func(t *testing.T) {
		testAuthLogin(t, habPath, configDir)
	})

	t.Run("AuthStatus", func(t *testing.T) {
		testAuthStatus(t, habPath, configDir)
	})

	t.Run("SystemInfo", func(t *testing.T) {
		testSystemInfo(t, habPath, configDir)
	})

	t.Run("SystemHealth", func(t *testing.T) {
		testSystemHealth(t, habPath, configDir)
	})

	t.Run("EntityList", func(t *testing.T) {
		testEntityList(t, habPath, configDir)
	})

	t.Run("AreaCRUD", func(t *testing.T) {
		testAreaCRUD(t, habPath, configDir)
	})

	t.Run("FloorCRUD", func(t *testing.T) {
		testFloorCRUD(t, habPath, configDir)
	})

	t.Run("LabelCRUD", func(t *testing.T) {
		testLabelCRUD(t, habPath, configDir)
	})

	t.Run("ActionList", func(t *testing.T) {
		testActionList(t, habPath, configDir)
	})

	t.Run("TextOutput", func(t *testing.T) {
		testTextOutput(t, habPath, configDir)
	})

	t.Run("AuthLogout", func(t *testing.T) {
		testAuthLogout(t, habPath, configDir)
	})
}

func buildCLI(t *testing.T) string {
	t.Helper()

	// Get the project root directory
	projectRoot, err := filepath.Abs("..")
	if err != nil {
		t.Fatalf("Failed to get project root: %v", err)
	}

	// Build to a temp file
	habPath := filepath.Join(os.TempDir(), fmt.Sprintf("hab-test-%d", time.Now().UnixNano()))

	cmd := exec.Command("go", "build", "-o", habPath, ".")
	cmd.Dir = projectRoot
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("Failed to build CLI: %v\n%s", err, output)
	}

	return habPath
}

func startEmptyHass(ctx context.Context, t *testing.T) *exec.Cmd {
	t.Helper()

	cmd := exec.CommandContext(ctx, "uvx", "--from", "git+https://github.com/balloob/empty-hass", "empty-hass")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Start(); err != nil {
		t.Fatalf("Failed to start empty-hass: %v", err)
	}

	return cmd
}

func waitForEmptyHass(t *testing.T) {
	t.Helper()

	client := &http.Client{Timeout: 2 * time.Second}
	maxAttempts := 60 // Wait up to 2 minutes

	for i := 0; i < maxAttempts; i++ {
		req, _ := http.NewRequest("GET", EmptyHassURL+"/api/", nil)
		req.Header.Set("Authorization", "Bearer "+EmptyHassToken)

		resp, err := client.Do(req)
		if err == nil && resp.StatusCode == 200 {
			resp.Body.Close()
			t.Log("empty-hass is ready")
			return
		}
		if resp != nil {
			resp.Body.Close()
		}

		time.Sleep(2 * time.Second)
	}

	t.Fatal("empty-hass did not become ready in time")
}

func runHab(t *testing.T, habPath, configDir string, args ...string) (string, error) {
	t.Helper()

	fullArgs := append([]string{"--config", configDir}, args...)
	cmd := exec.Command(habPath, fullArgs...)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	output := stdout.String()

	if stderr.Len() > 0 {
		t.Logf("stderr: %s", stderr.String())
	}

	return output, err
}

func parseJSONResponse(t *testing.T, output string) map[string]interface{} {
	t.Helper()

	var result map[string]interface{}
	if err := json.Unmarshal([]byte(output), &result); err != nil {
		t.Fatalf("Failed to parse JSON response: %v\nOutput: %s", err, output)
	}
	return result
}

func assertSuccess(t *testing.T, resp map[string]interface{}) {
	t.Helper()

	success, ok := resp["success"].(bool)
	if !ok || !success {
		t.Errorf("Expected success=true, got: %v", resp)
	}
}

// Test cases

func testAuthLogin(t *testing.T, habPath, configDir string) {
	output, err := runHab(t, habPath, configDir,
		"auth", "login", "--token",
		"--url", EmptyHassURL,
		"--access-token", EmptyHassToken,
	)
	if err != nil {
		t.Fatalf("auth login failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)

	data, ok := resp["data"].(map[string]interface{})
	if !ok {
		t.Fatal("Expected data in response")
	}

	if data["url"] != EmptyHassURL {
		t.Errorf("Expected url=%s, got %v", EmptyHassURL, data["url"])
	}

	t.Logf("Logged in to: %v (version: %v)", data["location_name"], data["version"])
}

func testAuthStatus(t *testing.T, habPath, configDir string) {
	output, err := runHab(t, habPath, configDir, "auth", "status")
	if err != nil {
		t.Fatalf("auth status failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)

	data, ok := resp["data"].(map[string]interface{})
	if !ok {
		t.Fatal("Expected data in response")
	}

	if data["authenticated"] != true {
		t.Error("Expected authenticated=true")
	}

	if data["url"] != EmptyHassURL {
		t.Errorf("Expected url=%s, got %v", EmptyHassURL, data["url"])
	}
}

func testSystemInfo(t *testing.T, habPath, configDir string) {
	output, err := runHab(t, habPath, configDir, "system", "info")
	if err != nil {
		t.Fatalf("system info failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)

	data, ok := resp["data"].(map[string]interface{})
	if !ok {
		t.Fatal("Expected data in response")
	}

	// Check for expected fields
	if data["version"] == nil {
		t.Error("Expected version field")
	}

	t.Logf("Home Assistant version: %v", data["version"])
}

func testSystemHealth(t *testing.T, habPath, configDir string) {
	output, err := runHab(t, habPath, configDir, "system", "health")
	if err != nil {
		t.Fatalf("system health failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)
}

func testEntityList(t *testing.T, habPath, configDir string) {
	output, err := runHab(t, habPath, configDir, "entity", "list")
	if err != nil {
		t.Fatalf("entity list failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)

	// Data should be an array (could be empty for empty-hass)
	data := resp["data"]
	if data == nil {
		// Empty data is OK for empty-hass
		return
	}

	entities, ok := data.([]interface{})
	if !ok {
		t.Fatalf("Expected data to be an array, got: %T", data)
	}

	t.Logf("Found %d entities", len(entities))
}

func testAreaCRUD(t *testing.T, habPath, configDir string) {
	areaName := fmt.Sprintf("Test Area %d", time.Now().UnixNano())

	// Create
	output, err := runHab(t, habPath, configDir, "area", "create", areaName)
	if err != nil {
		t.Fatalf("area create failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)

	data, ok := resp["data"].(map[string]interface{})
	if !ok {
		t.Fatal("Expected data in response")
	}

	areaID, ok := data["area_id"].(string)
	if !ok || areaID == "" {
		t.Fatal("Expected area_id in response")
	}
	t.Logf("Created area: %s", areaID)

	// List
	output, err = runHab(t, habPath, configDir, "area", "list")
	if err != nil {
		t.Fatalf("area list failed: %v\nOutput: %s", err, output)
	}

	resp = parseJSONResponse(t, output)
	assertSuccess(t, resp)

	areas, ok := resp["data"].([]interface{})
	if !ok {
		t.Fatal("Expected data to be an array")
	}

	found := false
	for _, a := range areas {
		area, ok := a.(map[string]interface{})
		if ok && area["area_id"] == areaID {
			found = true
			break
		}
	}
	if !found {
		t.Error("Created area not found in list")
	}

	// Update
	newName := areaName + " Updated"
	output, err = runHab(t, habPath, configDir, "area", "update", areaID, "--name", newName)
	if err != nil {
		t.Fatalf("area update failed: %v\nOutput: %s", err, output)
	}

	resp = parseJSONResponse(t, output)
	assertSuccess(t, resp)

	// Delete
	output, err = runHab(t, habPath, configDir, "area", "delete", areaID, "--force")
	if err != nil {
		t.Fatalf("area delete failed: %v\nOutput: %s", err, output)
	}

	resp = parseJSONResponse(t, output)
	assertSuccess(t, resp)
	t.Logf("Deleted area: %s", areaID)
}

func testFloorCRUD(t *testing.T, habPath, configDir string) {
	floorName := fmt.Sprintf("Test Floor %d", time.Now().UnixNano())

	// Create
	output, err := runHab(t, habPath, configDir, "floor", "create", floorName, "--level", "1")
	if err != nil {
		t.Fatalf("floor create failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)

	data, ok := resp["data"].(map[string]interface{})
	if !ok {
		t.Fatal("Expected data in response")
	}

	floorID, ok := data["floor_id"].(string)
	if !ok || floorID == "" {
		t.Fatal("Expected floor_id in response")
	}
	t.Logf("Created floor: %s", floorID)

	// List
	output, err = runHab(t, habPath, configDir, "floor", "list")
	if err != nil {
		t.Fatalf("floor list failed: %v\nOutput: %s", err, output)
	}

	resp = parseJSONResponse(t, output)
	assertSuccess(t, resp)

	// Delete
	output, err = runHab(t, habPath, configDir, "floor", "delete", floorID, "--force")
	if err != nil {
		t.Fatalf("floor delete failed: %v\nOutput: %s", err, output)
	}

	resp = parseJSONResponse(t, output)
	assertSuccess(t, resp)
	t.Logf("Deleted floor: %s", floorID)
}

func testLabelCRUD(t *testing.T, habPath, configDir string) {
	labelName := fmt.Sprintf("Test Label %d", time.Now().UnixNano())

	// Create
	output, err := runHab(t, habPath, configDir, "label", "create", labelName, "--color", "red")
	if err != nil {
		t.Fatalf("label create failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)

	data, ok := resp["data"].(map[string]interface{})
	if !ok {
		t.Fatal("Expected data in response")
	}

	labelID, ok := data["label_id"].(string)
	if !ok || labelID == "" {
		t.Fatal("Expected label_id in response")
	}
	t.Logf("Created label: %s", labelID)

	// List
	output, err = runHab(t, habPath, configDir, "label", "list")
	if err != nil {
		t.Fatalf("label list failed: %v\nOutput: %s", err, output)
	}

	resp = parseJSONResponse(t, output)
	assertSuccess(t, resp)

	// Delete
	output, err = runHab(t, habPath, configDir, "label", "delete", labelID, "--force")
	if err != nil {
		t.Fatalf("label delete failed: %v\nOutput: %s", err, output)
	}

	resp = parseJSONResponse(t, output)
	assertSuccess(t, resp)
	t.Logf("Deleted label: %s", labelID)
}

func testActionList(t *testing.T, habPath, configDir string) {
	output, err := runHab(t, habPath, configDir, "action", "list")
	if err != nil {
		t.Fatalf("action list failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)

	actions, ok := resp["data"].([]interface{})
	if !ok {
		t.Fatal("Expected data to be an array")
	}

	// Should have at least some actions (homeassistant.restart, etc.)
	if len(actions) == 0 {
		t.Error("Expected at least one action")
	}

	t.Logf("Found %d actions", len(actions))
}

func testTextOutput(t *testing.T, habPath, configDir string) {
	output, err := runHab(t, habPath, configDir, "--text", "system", "info")
	if err != nil {
		t.Fatalf("system info --text failed: %v\nOutput: %s", err, output)
	}

	// Text output should NOT be valid JSON
	var result map[string]interface{}
	if err := json.Unmarshal([]byte(output), &result); err == nil {
		t.Error("Expected text output, but got valid JSON")
	}

	// Should contain some expected text
	if !strings.Contains(output, "Version") && !strings.Contains(output, "version") {
		t.Error("Expected text output to contain version info")
	}

	t.Logf("Text output:\n%s", output)
}

func testAuthLogout(t *testing.T, habPath, configDir string) {
	output, err := runHab(t, habPath, configDir, "auth", "logout")
	if err != nil {
		t.Fatalf("auth logout failed: %v\nOutput: %s", err, output)
	}

	resp := parseJSONResponse(t, output)
	assertSuccess(t, resp)

	// Verify we're logged out
	output, err = runHab(t, habPath, configDir, "auth", "status")
	if err != nil {
		t.Fatalf("auth status failed: %v\nOutput: %s", err, output)
	}

	resp = parseJSONResponse(t, output)
	assertSuccess(t, resp)

	data, ok := resp["data"].(map[string]interface{})
	if !ok {
		t.Fatal("Expected data in response")
	}

	if data["authenticated"] != false {
		t.Error("Expected authenticated=false after logout")
	}
}
