# Offline schema provenance

Retrieved on October 1, 2026 from the published schemas linked by OpenAI's [plugin packaging documentation](https://developers.openai.com/plugins/build/plugins):

| Local snapshot | Official source | SHA-256 of this normalized snapshot |
| --- | --- | --- |
| `official/plugin.schema.json` | [Agent Plugins manifest schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json) | `bd0cfd6388f7d5c5c1b4c5edd70df030276345df115274686a0e6d52a92366ed` |
| `official/mcp.schema.json` | [Agent Plugins MCP schema](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json) | `2d4b2b9d1c95e75a356152534d2071f18094c1ee9be2eec238c91a1e1f9bd115` |

The web retrieval supplied the complete JSON bodies. These files preserve those JSON values, formatted with two spaces and a final newline. The hashes identify the checked-in normalized files, not the original HTTP response bytes. `package_validator.py` verifies the snapshots and validates both manifests with `jsonschema.Draft202012Validator`, without fetching remote schemas.

The portable manifest schema treats extension contents as arbitrary objects. OpenAI listing fields, review cases, path containment, icon dimensions, skill frontmatter and this plugin's four-tool boundary are checked separately. Neither schema validation nor those structural checks certify public deployment, legal adoption, third-party authorization, directory approval, or Google verification. Schema files are development evidence and stay outside the user ZIP.
