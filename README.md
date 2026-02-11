# Claude Memory MCP Server

This is a local Model Context Protocol (MCP) server that provides a persistent memory bank for Claude using ChromaDB. It allows Claude to store, retrieve, and manage learnings across different sessions and projects.

## Features

- **Persistent Storage**: Uses ChromaDB to store learnings locally in `~/.claude-memory/chroma_data`.
- **Semantic Search**: Learnings are retrieved based on semantic similarity to the query.
- **Project/Topic Organization**: Learnings can be tagged with topics and associated with specific codebases.
- **CRUD Operations**: Tools to store, query, list, and delete learnings.

## Prerequisites

- **Python 3.10** or higher
- **pip** (Python package installer)

## Installation & Setup

1. **Prepare the Directory**
    Ensure you have the server code in `~/.claude-memory`.

    ```bash
    mkdir -p ~/.claude-memory
    # Copy server.py and requirements.txt to this directory
    cd ~/.claude-memory
    ```

2. **Create a Virtual Environment** (Recommended)
    It's best to use a virtual environment to manage dependencies and avoid conflicts.

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install Dependencies**
    Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

    *Note: `requirements.txt` should contain:*

    ```text
    chromadb>=0.4.0
    mcp[cli]>=1.0.0
    ```

4. **Verify Installation**
    You can test if the server runs correctly:

    ```bash
    # This should start the MCP server (it communicates via stdio)
    python server.py
    # Press Ctrl+C to exit
    ```

## Configuration for Claude

To use this memory bank with Claude, you need to configure your MCP client (Claude Desktop or Claude Code) to recognize this server.

### 1. Configure the MCP Server

Add the following configuration to your Claude configuration file.

**For Claude Desktop:**
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "memory": {
      "command": "/Users/YOUR_USERNAME/.claude-memory/venv/bin/python",
      "args": ["/Users/YOUR_USERNAME/.claude-memory/server.py"]
    }
  }
}
```

**Note:** Replace `YOUR_USERNAME` with your actual username. Using the absolute path to the Python executable in your virtual environment (`venv/bin/python`) ensures the correct dependencies are loaded.

### 2. Set Up the System Prompt

To ensure Claude uses the memory bank effecitvely, add the following system prompt instructions to your `~/.claude/CLAUDE.md` (or your project-specific instruction file).

```markdown
You have access to a memory MCP server connected to a local chromadb instance. Let's call it memory bank from now on. Use this memory bank to enhance your knowledge and continuity across projects.

During each session:

- **Store new learnings** relevant to the current project using the `store_learning` tool.
- **Retrieve relevant past learnings** as needed by using the `query_learnings` or `list_recent_learnings` tools to inform your current reasoning and responses.
- **Delete outdated or irrelevant learnings** using the `delete_learning` tool to keep the memory bank up to date.
- **Monitor and summarize** your stored knowledge per project with the `get_learning_stats` tool.

Always prioritize using the MCP memory tools to ensure your responses are informed by previous knowledge and remain project-specific.
If you are unsure about prior context or need additional information, query the memory bank via MCP tools before proceeding.

**Available MCP Tools:**
1. `store_learning` – Save new insights or knowledge for the current project.
2. `query_learnings` – Search for relevant past learnings.
3. `list_recent_learnings` – Review your most recent learnings.
4. `delete_learning` – Remove outdated or incorrect learnings.
5. `get_learning_stats` – Summarize or analyze your stored knowledge.

**Instructions:**
1. If during your session:
    * You have to start an investigation or exploring code base
    * Look for unknown knowledge or information
... then first check the memory bank if there's any useful information there you can use to speed up your process.

2. If during your session:
    * You learned something new about the project
    * I corrected you on a specific implementation detail
    * I corrected source code you generated
    * You struggled to find specific information and had to infer details about the project
    * You lost track of the project structure and had to look up information in the source code
...that is relevant, was not known initially, and should be persisted, add it to the memory bank via MCP tools. This ensures important knowledge is retained and available in future sessions.
```

## Maintenance

- **Data Location**: All data is stored in `~/.claude-memory/chroma_data`.
- **Resetting Memory**: To clear all memory, you can simply delete the `chroma_data` directory (make sure no processes are using it).

  ```bash
  rm -rf ~/.claude-memory/chroma_data
  ```
