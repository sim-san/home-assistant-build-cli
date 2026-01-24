# Home Assistant Builder (hab) - Specification

A CLI utility designed for LLMs to build and manage Home Assistant configurations.

## Design Philosophy

This CLI is optimized for **LLM consumption**. Key principles:

1. **Hierarchical Help**: Top-level `--help` shows command groups, not all sub-commands
2. **Indexed Documentation**: Each command group has its own `--help` with detailed sub-commands
3. **Structured Output**: JSON output by default for easy parsing
4. **Explicit Errors**: Clear, actionable error messages

## Authentication

### Configuration Location

Secrets are stored in `~/.config/home-assistant-builder/`:

```
~/.config/home-assistant-builder/
├── config.json          # General configuration
├── credentials.json     # Encrypted credentials (OAuth tokens)
└── .env                 # Environment variable overrides (optional)
```

### Authentication Methods

Authentication is resolved in the following order:

1. **Environment Variables** (highest priority)
   - `HAB_URL` - Home Assistant URL
   - `HAB_TOKEN` - Long-lived access token
   - `HAB_REFRESH_TOKEN` - OAuth refresh token (if using OAuth flow)

2. **Secrets File** (`~/.config/home-assistant-builder/credentials.json`)
   - Stores encrypted OAuth tokens or long-lived access tokens
   - Encrypted using a key derived from machine-specific identifiers

3. **Interactive Login** (fallback)
   - `hab auth login` - Initiates OAuth flow or token input

### OAuth2 Flow

The OAuth2 flow uses Home Assistant's built-in OAuth provider:

1. User runs `hab auth login`
2. CLI starts a temporary HTTP server on a random available port
3. Server binds to network IP (not localhost) for SSH compatibility
4. Opens browser to Home Assistant authorization URL
5. User authorizes in Home Assistant
6. Home Assistant redirects to temporary server with authorization code
7. CLI exchanges code for access + refresh tokens
8. Tokens are stored encrypted in credentials.json
9. Temporary server shuts down

**Redirect URI**: `http://<network-ip>:<random-port>/callback`

### Long-Lived Access Token

For environments where OAuth is not practical:

```bash
hab auth login --token
# Prompts for URL and token interactively

hab auth login --token --url https://ha.local:8123 --access-token "eyJ..."
# Non-interactive mode
```

### Token Refresh

- OAuth tokens are automatically refreshed when expired
- If refresh fails, user is prompted to re-authenticate
- Long-lived access tokens do not expire (no refresh needed)

## CLI Structure

### Top-Level Help

```
$ hab --help

Home Assistant Builder - Build Home Assistant configurations

Usage: hab <command> [options]

Commands:
  auth          Authentication management
  automation    Manage automations
  script        Manage scripts
  entity        Entity operations
  action        Call actions
  area          Manage areas
  floor         Manage floors
  zone          Manage zones
  label         Manage labels
  helper        Manage helper entities
  dashboard     Manage dashboards
  backup        Backup and restore
  calendar      Manage calendar events
  blueprint     Manage blueprints
  system        System operations
  device        Device management
  group         Manage entity groups
  thread        Manage Thread credentials

Options:
  --help, -h    Show this help message
  --version     Show version
  --json        Force JSON output (default)
  --text        Use human-readable text output
  --verbose     Show verbose output
  --config      Path to config directory (default: ~/.config/home-assistant-builder)

Run 'hab <command> --help' for more information on a command.
```

### Command Group Help Example

```
$ hab automation --help

Manage Home Assistant automations

Usage: hab automation <subcommand> [options]

Subcommands:
  list          List all automations
  get           Get automation configuration by ID
  create        Create a new automation
  update        Update an existing automation
  delete        Delete an automation
  trigger       Manually trigger an automation
  trace         Get execution traces for debugging

Run 'hab automation <subcommand> --help' for subcommand details.
```

## Commands Reference

### auth - Authentication Management

| Subcommand | Description |
|------------|-------------|
| `login` | Authenticate with Home Assistant (OAuth or token) |
| `logout` | Remove stored credentials |
| `status` | Show current authentication status |
| `refresh` | Force token refresh (OAuth only) |

### automation - Manage Automations

| Subcommand | Description |
|------------|-------------|
| `list` | List all automations with optional filtering |
| `get <id>` | Get full automation configuration |
| `create` | Create a new automation from YAML/JSON |
| `update <id>` | Update an existing automation |
| `delete <id>` | Delete an automation |
| `trigger <id>` | Manually trigger an automation |
| `trace <id>` | Get execution traces for debugging |

### script - Manage Scripts

| Subcommand | Description |
|------------|-------------|
| `list` | List all scripts |
| `get <id>` | Get script configuration |
| `create` | Create a new script |
| `update <id>` | Update an existing script |
| `delete <id>` | Delete a script |
| `run <id>` | Execute a script |

### entity - Entity Operations

| Subcommand | Description |
|------------|-------------|
| `list` | List entities with optional domain/area filtering |
| `get <entity_id>` | Get entity state and attributes |
| `search <query>` | Fuzzy search for entities |
| `history <entity_id>` | Get state history |
| `rename <entity_id>` | Rename an entity |
| `enable <entity_id>` | Enable a disabled entity |
| `disable <entity_id>` | Disable an entity |

### action - Call Actions

| Subcommand | Description |
|------------|-------------|
| `list [domain]` | List available actions |
| `call <domain.action>` | Call an action with data |
| `docs <domain.action>` | Show action documentation |

### area - Manage Areas

| Subcommand | Description |
|------------|-------------|
| `list` | List all areas |
| `create <name>` | Create a new area |
| `update <id>` | Update an area |
| `delete <id>` | Delete an area |

### floor - Manage Floors

| Subcommand | Description |
|------------|-------------|
| `list` | List all floors |
| `create <name>` | Create a new floor |
| `update <id>` | Update a floor |
| `delete <id>` | Delete a floor |

### zone - Manage Zones

| Subcommand | Description |
|------------|-------------|
| `list` | List all zones |
| `create` | Create a new zone |
| `update <id>` | Update a zone |
| `delete <id>` | Delete a zone |

### label - Manage Labels

| Subcommand | Description |
|------------|-------------|
| `list` | List all labels |
| `create <name>` | Create a new label |
| `update <id>` | Update a label |
| `delete <id>` | Delete a label |
| `assign <label> <entity_id>` | Assign label to entity |
| `remove <label> <entity_id>` | Remove label from entity |

### helper - Manage Helper Entities

| Subcommand | Description |
|------------|-------------|
| `list [type]` | List helper entities |
| `create <type>` | Create a helper (boolean, number, text, select, datetime, button, counter, timer, schedule) |
| `update <entity_id>` | Update a helper |
| `delete <entity_id>` | Delete a helper |

### dashboard - Manage Dashboards

| Subcommand | Description |
|------------|-------------|
| `list` | List all dashboards |
| `get <url_path>` | Get dashboard configuration |
| `create` | Create a new dashboard |
| `update <url_path>` | Update a dashboard |
| `delete <url_path>` | Delete a dashboard |
| `card-types` | List available card types with documentation |

### backup - Backup and Restore

| Subcommand | Description |
|------------|-------------|
| `list` | List available backups |
| `create [name]` | Create a new backup |
| `restore <slug>` | Restore from a backup |
| `download <slug>` | Download a backup file |
| `delete <slug>` | Delete a backup |

### calendar - Manage Calendar Events

| Subcommand | Description |
|------------|-------------|
| `list <entity_id>` | List calendar events |
| `create <entity_id>` | Create a calendar event |
| `update <entity_id> <uid>` | Update a calendar event |
| `delete <entity_id> <uid>` | Delete a calendar event |

### blueprint - Manage Blueprints

| Subcommand | Description |
|------------|-------------|
| `list [domain]` | List blueprints (automation/script) |
| `import <url>` | Import a blueprint from URL |
| `get <path>` | Get blueprint configuration |

### system - System Operations

| Subcommand | Description |
|------------|-------------|
| `info` | Get system information |
| `health` | Get system health status |
| `config-check` | Validate configuration |
| `restart` | Restart Home Assistant |
| `logs` | Get error logs |
| `updates` | Check for available updates |

### device - Device Management

| Subcommand | Description |
|------------|-------------|
| `list` | List all devices |
| `get <device_id>` | Get device details |
| `delete <device_id>` | Delete a device |
| `entities <device_id>` | List entities for a device |

### group - Manage Entity Groups

| Subcommand | Description |
|------------|-------------|
| `list` | List all groups |
| `create` | Create a new group |
| `update <id>` | Update a group |
| `delete <id>` | Delete a group |

### thread - Manage Thread Credentials

| Subcommand | Description |
|------------|-------------|
| `list` | List all Thread datasets |
| `get <dataset_id>` | Get dataset details including TLV |
| `add` | Add a new Thread dataset from TLV |
| `delete <dataset_id>` | Delete a Thread dataset |
| `set-preferred <dataset_id>` | Set a dataset as the preferred network |

## Output Format

### JSON Output (Default)

All commands output JSON by default for LLM consumption:

```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "abc123"
  }
}
```

### Error Output

```json
{
  "success": false,
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Entity 'light.nonexistent' was not found",
    "details": {
      "entity_id": "light.nonexistent",
      "suggestion": "Did you mean 'light.living_room'?"
    }
  }
}
```

### Text Output

When `--text` is specified, output is human-readable:

```
$ hab entity get light.living_room --text

Entity: light.living_room
State: on
Attributes:
  brightness: 255
  color_temp: 370
  friendly_name: Living Room Light
```

## Input Format

### Piped Input

Commands accept JSON input via stdin:

```bash
echo '{"alias": "My Automation", "trigger": [...]}' | hab automation create

cat automation.yaml | hab automation create --format yaml
```

### File Input

```bash
hab automation create --file automation.yaml
hab automation create --file automation.json
```

### Inline Data

```bash
hab action call light.turn_on --data '{"entity_id": "light.living_room", "brightness": 200}'
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Authentication error |
| 4 | Resource not found |
| 5 | Permission denied |
| 6 | Connection error |
| 7 | Validation error |
| 8 | Timeout |

## Implementation Details

### Technology Stack

- **Language**: Python 3.11+
- **CLI Framework**: Click
- **HTTP Client**: httpx (async support)
- **WebSocket**: websockets
- **OAuth Server**: Built-in http.server
- **Configuration**: platformdirs + pydantic
- **Encryption**: cryptography (Fernet)
- **Packaging**: uv for dependency management

### Project Structure

```
src/
└── hab/
    ├── __init__.py
    ├── __main__.py           # Entry point (python -m hab)
    ├── cli/
    │   ├── __init__.py       # Click group setup
    │   ├── main.py           # Main CLI entry
    │   └── commands/         # Command implementations
    │       ├── __init__.py
    │       ├── auth.py
    │       ├── automation.py
    │       ├── action.py
    │       ├── script.py
    │       ├── entity.py
    │       └── ...
    ├── client/
    │   ├── __init__.py
    │   ├── rest.py           # REST API client
    │   ├── websocket.py      # WebSocket client
    │   └── models.py         # Pydantic models
    ├── auth/
    │   ├── __init__.py
    │   ├── manager.py        # Auth state management
    │   ├── oauth.py          # OAuth flow
    │   ├── server.py         # Temporary OAuth callback server
    │   └── credentials.py    # Credential storage
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py       # Configuration management
    │   └── paths.py          # Config file paths (platformdirs)
    └── utils/
        ├── __init__.py
        ├── output.py         # JSON/text formatting
        └── input.py          # Input parsing (YAML/JSON)
```

### API Endpoints Used

Based on Home Assistant's REST and WebSocket APIs:

**REST API** (`/api/...`):
- `/api/config` - Configuration
- `/api/states` - Entity states
- `/api/services` - Action calls
- `/api/history/period` - History data
- `/api/logbook` - Event logs
- `/api/config/automation/config/{id}` - Automation CRUD
- `/api/config/script/config/{id}` - Script CRUD
- `/api/template` - Template rendering
- And more...

**WebSocket API** (`/api/websocket`):
- Real-time state updates
- Area/floor/zone/label management
- Device registry operations
- Config entry management

### Reference Implementations

For inspiration when implementing commands, refer to:

- **Home Assistant Frontend**: `../../hass/frontend/src/data/` - TypeScript modules showing API calls and data structures for each feature (e.g., `thread.ts`, `automation.ts`, `area_registry.ts`)
- **Home Assistant JS WebSocket**: `../../hass/home-assistant-js-websocket/` - Modern WebSocket patterns including core entity subscriptions
- **Home Assistant MCP**: `../ha-mcp/src/ha_mcp/tools/` - Python tool implementations with similar patterns (e.g., `tools_labels.py`, `tools_config_automations.py`)

## Security Considerations

1. **Credential Storage**: Credentials are encrypted at rest using AES-256-GCM
2. **Network IP**: OAuth callback uses network IP, not localhost
3. **Temporary Server**: OAuth server runs only during authentication, auto-closes after 5 minutes
4. **Token Scope**: OAuth tokens are scoped to the authenticated user's permissions
5. **No Token Logging**: Tokens are never logged or included in error messages

## Future Enhancements

- [ ] WebSocket real-time subscriptions (`hab subscribe <entity_id>`)
- [ ] Batch operations (`hab batch < commands.json`)
- [ ] Profile management for multiple HA instances
- [ ] Plugin system for custom commands
- [ ] Shell completion scripts (bash, zsh, fish)
- [ ] Integration with VS Code extension
