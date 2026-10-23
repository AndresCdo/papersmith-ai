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
    }
  }
}
