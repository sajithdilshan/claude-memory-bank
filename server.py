#!/usr/bin/env python3
"""
Claude Memory MCP Server

A local MCP server that stores and retrieves learnings using ChromaDB
for semantic search. Learnings persist across sessions.
"""

import os
import json
from datetime import datetime
from typing import Any

import chromadb
from chromadb.config import Settings
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("claude-memory")

# Initialize ChromaDB with persistent storage
CHROMA_PATH = os.path.expanduser("~/.claude-memory/chroma_data")
chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH,
    settings=Settings(anonymized_telemetry=False),
)

# Get or create the learnings collection
collection = chroma_client.get_or_create_collection(
    name="learnings",
    metadata={"description": "Claude's learnings across sessions"},
)


@mcp.tool()
def store_learning(
    content: str,
    topic: str,
    codebase: str | None = None,
    tags: list[str] | None = None,
) -> str:
    """
    Store a new learning in the memory database.

    Args:
        content: The learning content to store (what was learned)
        topic: The topic/category of the learning (e.g., "architecture", "testing", "debugging")
        codebase: Optional - which codebase this relates to
        tags: Optional - additional tags for categorization

    Returns:
        Confirmation message with the learning ID
    """
    learning_id = f"learning_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    metadata = {
        "topic": topic,
        "codebase": codebase or "general",
        "tags": json.dumps(tags or []),
        "created_at": datetime.now().isoformat(),
    }

    collection.add(
        ids=[learning_id],
        documents=[content],
        metadatas=[metadata],
    )

    return f"Stored learning with ID: {learning_id}"


@mcp.tool()
def query_learnings(
    query: str,
    n_results: int = 5,
    topic: str | None = None,
    codebase: str | None = None,
) -> str:
    """
    Search for relevant learnings using semantic search.

    Args:
        query: The search query - describe what you're looking for
        n_results: Number of results to return (default: 5)
        topic: Optional - filter by topic
        codebase: Optional - filter by codebase

    Returns:
        Relevant learnings with their metadata
    """
    # Build where filter if topic or codebase specified
    where_filter = None
    if topic or codebase:
        conditions = []
        if topic:
            conditions.append({"topic": topic})
        if codebase:
            conditions.append({"codebase": codebase})

        if len(conditions) == 1:
            where_filter = conditions[0]
        else:
            where_filter = {"$and": conditions}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter,
    )

    if not results["ids"] or not results["ids"][0]:
        return "No relevant learnings found."

    output = []
    for i, (doc_id, document, metadata) in enumerate(
        zip(results["ids"][0], results["documents"][0], results["metadatas"][0])
    ):
        tags = json.loads(metadata.get("tags", "[]"))
        output.append(
            f"### Result {i + 1}\n"
            f"**ID:** {doc_id}\n"
            f"**Topic:** {metadata.get('topic', 'N/A')}\n"
            f"**Codebase:** {metadata.get('codebase', 'N/A')}\n"
            f"**Tags:** {', '.join(tags) if tags else 'None'}\n"
            f"**Created:** {metadata.get('created_at', 'N/A')}\n"
            f"**Content:**\n{document}\n"
        )

    return "\n---\n".join(output)


@mcp.tool()
def list_recent_learnings(n_results: int = 10, codebase: str | None = None) -> str:
    """
    List the most recent learnings.

    Args:
        n_results: Number of recent learnings to return (default: 10)
        codebase: Optional - filter by codebase

    Returns:
        List of recent learnings with their metadata
    """
    where_filter = {"codebase": codebase} if codebase else None

    # Get all learnings (ChromaDB doesn't have great sorting, so we fetch and sort)
    results = collection.get(
        where=where_filter,
        include=["documents", "metadatas"],
    )

    if not results["ids"]:
        return "No learnings stored yet."

    # Sort by created_at descending
    items = list(zip(results["ids"], results["documents"], results["metadatas"]))
    items.sort(key=lambda x: x[2].get("created_at", ""), reverse=True)
    items = items[:n_results]

    output = []
    for doc_id, document, metadata in items:
        tags = json.loads(metadata.get("tags", "[]"))
        # Truncate content for listing
        content_preview = document[:200] + "..." if len(document) > 200 else document
        output.append(
            f"**ID:** {doc_id}\n"
            f"**Topic:** {metadata.get('topic', 'N/A')} | "
            f"**Codebase:** {metadata.get('codebase', 'N/A')}\n"
            f"**Created:** {metadata.get('created_at', 'N/A')}\n"
            f"**Preview:** {content_preview}\n"
        )

    return "\n---\n".join(output)


@mcp.tool()
def delete_learning(learning_id: str) -> str:
    """
    Delete a learning by its ID.

    Args:
        learning_id: The ID of the learning to delete

    Returns:
        Confirmation message
    """
    try:
        collection.delete(ids=[learning_id])
        return f"Deleted learning: {learning_id}"
    except Exception as e:
        return f"Error deleting learning: {e}"


@mcp.tool()
def get_learning_stats() -> str:
    """
    Get statistics about stored learnings.

    Returns:
        Statistics including total count, topics, and codebases
    """
    results = collection.get(include=["metadatas"])

    if not results["ids"]:
        return "No learnings stored yet."

    total = len(results["ids"])
    topics: dict[str, int] = {}
    codebases: dict[str, int] = {}

    for metadata in results["metadatas"]:
        topic = metadata.get("topic", "unknown")
        codebase = metadata.get("codebase", "general")
        topics[topic] = topics.get(topic, 0) + 1
        codebases[codebase] = codebases.get(codebase, 0) + 1

    output = [
        f"**Total Learnings:** {total}\n",
        "**By Topic:**",
    ]
    for topic, count in sorted(topics.items(), key=lambda x: -x[1]):
        output.append(f"  - {topic}: {count}")

    output.append("\n**By Codebase:**")
    for codebase, count in sorted(codebases.items(), key=lambda x: -x[1]):
        output.append(f"  - {codebase}: {count}")

    return "\n".join(output)


if __name__ == "__main__":
    mcp.run()
