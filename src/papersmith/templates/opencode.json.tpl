{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "bash": {
      "*": "allow"
    },
    "read": {
      "*": "allow"
    }
  },
  "mcp": {
    "banco-lia": {
      "type": "local",
      "command": [
        "uvx",
        "--from",
        "git+https://github.com/LIAUNAL/bancoProyectosPapersLIA",
        "banco-lia-mcp"
      ],
      "enabled": true
    },
    "kaggle": {
      "type": "remote",
      "url": "https://www.kaggle.com/mcp",
      "headers": {
        "Authorization": "Bearer {env:KAGGLE_API_TOKEN}"
      },
      "enabled": true
    }
  }
}
