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
cp config.json.example config.json

# Edit config.json with your Discord tokens
# {
#   "accounts": [
#     {
#       "token": "your_first_token_here",
#       "status": "dnd",
#       "custom_status": ""
#     }
#   ]
# }
```

3. **Run the container:**
```bash
docker run -d --name discord-onliner -v ./config.json:/app/config.json ghcr.io/armin-faldis/discord-onliner:main
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

### Configuration

Configure your Discord accounts in the `config.json` file:

- `token` - Your Discord user token (required)
- `status` - Status: "online", "idle", "dnd", or "invisible" (default: "dnd")
- `custom_status` - Custom status message (optional, leave empty string for none)

**Example config.json file:**
```json
{
  "accounts": [
    {
      "token": "your_first_token_here",
      "status": "dnd",
      "custom_status": ""
    },
    {
      "token": "your_second_token_here",
      "status": "online",
      "custom_status": "Gaming"
    }
  ]
}
```
