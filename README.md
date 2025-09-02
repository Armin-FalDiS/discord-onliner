## Docker

A pre-built Docker image is available on GitHub Container Registry for easy deployment.

### Quick Start

1. **Pull the image:**
```bash
docker pull ghcr.io/armin-faldis/discord-onliner:main
```

2. **Create your configuration:**
```bash
# Copy the example file
cp env.example .env

# Edit .env with your Discord tokens
# DISCORD_TOKEN_1=your_first_token_here
# DISCORD_STATUS_1=dnd
# DISCORD_CUSTOM_STATUS_1=
```

3. **Run the container:**
```bash
docker run -d --name discord-onliner --env-file .env ghcr.io/armin-faldis/discord-onliner:main
```

### Docker Commands

```bash
# View logs
docker logs discord-onliner

# Stop container
docker stop discord-onliner

# Remove container
docker rm discord-onliner

# Restart container
docker restart discord-onliner
```

### Environment Variables

Configure your Discord accounts in the `.env` file:

- `DISCORD_TOKEN_1`, `DISCORD_TOKEN_2`, etc. - Your Discord user tokens
- `DISCORD_STATUS_1`, `DISCORD_STATUS_2`, etc. - Status: "online", "idle", "dnd", or "invisible"
- `DISCORD_CUSTOM_STATUS_1`, `DISCORD_CUSTOM_STATUS_2`, etc. - Custom status messages (optional)

**Example .env file:**
```bash
DISCORD_TOKEN_1=your_first_token_here
DISCORD_STATUS_1=dnd
DISCORD_CUSTOM_STATUS_1=

DISCORD_TOKEN_2=your_second_token_here
DISCORD_STATUS_2=online
DISCORD_CUSTOM_STATUS_2=Gaming
```
