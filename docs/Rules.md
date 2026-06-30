# P.I.N.G.S Core v2 — Operational Rules

## 1. Safety First

### 1.1 Destructive Operations
Always confirm before executing:
- `rm -rf` on any directory
- `docker stop`, `docker rm`, `docker volume rm`
- `systemctl stop`, `systemctl disable`
- `apt remove`, `apt purge`
- `DROP TABLE`, `TRUNCATE`
- Any command that could cause data loss

### 1.2 SSH Safety
- Read-only commands (ls, cat, grep, df, free) → No confirmation needed
- Write commands (mkdir, touch, echo) → Confirm once
- Destructive commands (rm, stop, disable, drop) → Always confirm
- Connect to known hosts only

### 1.3 Secrets Management
- Never log, print, or expose API keys
- Never commit secrets to git
- Use environment variables for all credentials
- Rotate compromised secrets immediately

## 2. File Operations

### 2.1 Workspace Sandboxing
- All file operations default to /app/workspace
- Explicit permission required for other directories
- Use absolute paths when possible
- Verify parent directory exists before writing

### 2.2 File Safety
- Check file exists before reading
- Never overwrite without confirmation
- Use atomic writes where possible
- Keep backups of modified config files

## 3. Docker Operations

### 3.1 Container Management
- Always use `docker compose` for multi-service operations
- Check container health before assuming issues
- Use `docker compose logs <service>` for debugging
- Restart single services, not the whole stack

### 3.2 Volume Management
- Never remove volumes without explicit confirmation
- Back up volumes before migrations
- Monitor volume disk usage
- Use named volumes, not bind mounts for data

### 3.3 Network
- All services communicate via pings-net
- Do not expose internal service ports externally
- Use service names for inter-container communication

## 4. API Conventions

### 4.1 Request Handling
- Validate all input parameters
- Return appropriate HTTP status codes
- Include error messages in responses
- Log all errors with context

### 4.2 Response Format
- JSON for all API responses
- Consistent error structure
- Include request ID for tracing
- Paginate large result sets

## 5. AI Model Rules

### 5.1 Model Selection
- Default to MiMo V2.5 Free unless task requires specific model
- Research tasks → DeepSeek V4 Flash Free or Nemotron 3 Ultra Free
- Code tasks → North Mini Code Free
- Creative tasks → Big Pickle
- Vision tasks → NVIDIA NIM (nvidia/vila)

### 5.2 Response Quality
- Be concise and direct
- Provide actionable answers
- Include code examples when relevant
- Admit when unsure

## 6. Monitoring

### 6.1 Health Checks
- All services must pass healthchecks
- Monitor container resource usage
- Alert on service failures
- Track API response times

### 6.2 Logging
- Use structured logging (JSON)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Rotate logs to prevent disk fill
- Keep error logs for debugging

## 7. Backup Strategy

### 7.1 Data
- SQLite database: daily backup
- ChromaDB: weekly backup
- Configuration files: backup before changes
- Docker volumes: snapshot before upgrades

### 7.2 Recovery
- Document recovery procedures
- Test restores periodically
- Keep backups in separate location
- Version control all configuration

## 8. Communication Rules

### 8.1 With User
- Be concise — avoid unnecessary explanation
- Provide options when multiple paths exist
- Ask before assuming intent
- Report progress on long-running tasks

### 8.2 Error Reporting
- Include what happened
- Include what was attempted
- Suggest next steps
- Log full error details

## 9. Performance

### 9.1 API Response Times
- Status endpoint: < 100ms
- Chat message: < 5s
- Research start: < 2s
- File upload: < 30s

### 9.2 Resource Limits
- Container CPU: 2 cores max
- Container RAM: 2GB max
- File upload: 50MB max
- Conversation history: 1000 messages per session

## 10. Updates

### 10.1 Container Updates
- Check changelog before updating
- Test in development first
- Update one service at a time
- Monitor after update

### 10.2 Schema Changes
- Never drop tables in production
- Use migrations for schema changes
- Backup before migration
- Test migration on copy first
