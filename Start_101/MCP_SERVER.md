# Driving IxNetwork from Claude with an MCP server

## What it is

The **Model Context Protocol (MCP)** is an open standard that lets an AI assistant,
such as Claude Desktop or Claude Code, call external tools. An **IxNetwork MCP server**
is a small program that runs on your PC. It wraps the same REST API that RestPy uses
and exposes it as *tools* such as "create session", "load config", "start protocols",
"start traffic" and "get statistics".

So you can ask, in plain English:

> "Create a session on localhost, load configs/macsec_mka.ixncfg, map the ports to
> 10.80.81.2 card 2 ports 1 and 2, start protocols, check that MKA is up, run traffic
> for 30 seconds at 512 bytes, show me the traffic item stats, then delete the session."

Claude then plans the steps, calls the tools, and reports the results.

```
 You ──► Claude (Desktop / Code) ──MCP──► IxNetwork MCP server ──REST──► IxNetwork API server ──► Chassis/ports
```

## MCP or Python scripts?

| Use the MCP server for... | Use the Python scripts (this folder) for... |
|---|---|
| Exploring, ad-hoc checks, demos | Regression tests, CI/CD pipelines, nightly runs |
| "What is the loss on port 2 right now?" | Repeatable pass/fail with exact parameters |
| Learning: ask Claude to *show you the RestPy code* for what it just did | Version-controlled, reviewed test cases |
| Quick troubleshooting of a running session | Large parameter sweeps (frame sizes, rates, keys) |

They work well together: explore with MCP, then ask Claude to turn the session into a
script that follows the pattern of lessons 03–05.

## Setup

> The exact package name, start command and tool names depend on the IxNetwork MCP
> server build you were given. Replace the `<...>` placeholders with the values from
> its README.

### 1. Install the server

```bash
pip install <ixnetwork-mcp-package>
```

### 2a. Register it with Claude Code (CLI)

```bash
claude mcp add ixnetwork -e IXN_API_SERVER=localhost -e IXN_CHASSIS=10.80.81.2 -- <ixnetwork-mcp-command>
```

```bash
claude mcp list
```

### 2b. Register it with Claude Desktop

Edit `claude_desktop_config.json`:

* **Windows:** `%APPDATA%\Claude\`
* **macOS:** `~/Library/Application Support/Claude/`

```json
{
  "mcpServers": {
    "ixnetwork": {
      "command": "<ixnetwork-mcp-command>",
      "args": [],
      "env": {
        "IXN_API_SERVER": "localhost",
        "IXN_CHASSIS": "10.80.81.2",
        "IXN_USERNAME": "admin",
        "IXN_PASSWORD": "<set-me>"
      }
    }
  }
}
```

Restart Claude Desktop. The IxNetwork tools then appear in the tools (🔨) menu.

### 3. Give Claude your lab context

Put a `CLAUDE.md` file in your working folder. Claude reads it at the start of every
session:

```markdown
# Lab
- IxNetwork API server: localhost
- Chassis: 10.80.81.2, ports 2/1-2/4 -> DUT (NXP TSN switch, 10.80.81.6), 1G copper
- Always delete the IxNetwork session when done (limited licenses)
- Use a unique, identifiable session name (e.g. mcp-<user>-<date>)
- Save captures/configs/reports into this folder
```

## Example prompts

* *"List the sessions on the API server and tell me who owns them."*
* *"Create a session called mcp-demo-<today>, connect ports 2/1 and 2/2, and show me
  their link state and speed."*
* *"Build two MACsec static-SAK endpoints with key f123…cdef, send 100k frames at 64,
  512 and 1500 bytes, and give me a table of Tx/Rx/loss per size."*
* *"Start protocols and tell me if MKA elected a key server. Which side, and which
  cipher suite?"*
* *"Capture 10 seconds on port 2, download the .cap here, and summarise the protocols
  you see."*
* *"Write me a RestPy script that reproduces exactly what you just did."*
* *"We're done. Stop everything and delete the session."*

## Good practice

* **Licenses.** Each session uses a license, and labs often have only a few. Always end
  with *"delete the session"*. Before you create a new session, check for leftover ones
  with *"list sessions"*.
* **Review before running.** Claude shows each tool call before it runs. Read the
  destructive ones, such as clearing a config, taking ownership of ports, or deleting
  sessions.
* **Shared chassis.** Taking port ownership forcibly kicks out other users. Tell Claude
  which ports are yours, in `CLAUDE.md` or in the prompt.
* **Credentials.** Put them in environment variables or the MCP `env` block, never in
  the prompt or in committed files.
