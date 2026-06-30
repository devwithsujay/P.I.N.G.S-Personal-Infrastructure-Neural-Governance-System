# P.I.N.G.S Safety Rules

## Destructive Operation Confirmation

Always confirm with the owner before executing ANY of the following:

### File System
- `rm -rf` on any directory
- `rm` on critical config files (/etc/*, ~/.ssh/*, ~/.config/*)
- Overwriting existing files without explicit instruction
- Moving or renaming files in production paths

### Docker
- `docker stop` on any running container
- `docker rm` on any container
- `docker volume rm` on any volume
- `docker network rm` on any network
- `docker compose down` (stops and removes all services)
- Removing images with `docker rmi`

### System Services
- `systemctl stop` on any running service
- `systemctl disable` on any service
- `systemctl restart` on critical services (nginx, docker, ssh)

### Package Management
- `apt remove` or `apt purge` on any package
- `pip uninstall` on any package
- `npm uninstall` on any package
- Updating system packages without confirmation

### SSH / Remote
- SSH commands that modify remote systems
- Destructive commands executed via SSH (`rm`, `drop`, `kill`)
- SSH into production servers without specifying the target

### Database
- `DROP TABLE` or `DROP DATABASE` statements
- Truncating tables
- Deleting all records without a WHERE clause

## Secrets and Credentials

- NEVER log, print, or expose API keys, tokens, or passwords
- NEVER commit secrets to version control
- NEVER include secrets in chat responses
- ALWAYS use environment variables or secret managers
- If a secret is accidentally exposed, flag it immediately and advise rotation

## File Operations

- Sandbox all file operations to `/app/workspace` unless explicitly told otherwise
- Use absolute paths when possible
- Verify file exists before reading
- Check parent directory exists before writing

## SSH Safety

- Confirm the target host before connecting
- For destructive commands (rm, stop, disable, drop), always confirm
- Read-only commands (ls, cat, grep, df, free, top) can proceed without confirmation
- Prefer read-only commands first to understand the state before making changes

## Error Handling

- If a command fails, stop and report the error
- Never silently retry destructive commands
- Log all errors with context
- Provide the owner with options for recovery

## Scope

- These rules apply to all interactions with P.I.N.G.S
- Rules can be updated by the owner at any time
- When in doubt, ask before acting
