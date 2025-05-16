"""tools.memory

Provides MemoryTool for interacting with the shared ContextBus memory store.
"""
from __future__ import annotations

from .base import Tool, ToolInput, ToolOutput
from .registry import ToolRegistry
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os

CHROMA_PATH = os.path.join("agent_workspace", "chroma_db")
COLLECTION_NAME = "agent_memory"

# Use a simple embedding function (Chroma provides some, or stub for tests)
EMBEDDING_FN = embedding_functions.DefaultEmbeddingFunction()

class ChromaMemoryTool(Tool):
    def __init__(self):
        self.client = chromadb.Client(Settings(
            persist_directory=CHROMA_PATH,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            COLLECTION_NAME, embedding_function=EMBEDDING_FN
        )

    def execute(self, tool_input: ToolInput) -> ToolOutput:
        op = tool_input.operation_name.lower().strip()
        args = tool_input.args or {}
        if op == "remember":
            text = args.get("text")
            if not text or not isinstance(text, str):
                return ToolOutput(success=False, error="/remember requires a text string.")
            # Use text as both id and content for simplicity
            self.collection.add(documents=[text], ids=[str(hash(text))])
            return ToolOutput(success=True, message=f"Remembered: {text}")
        elif op == "recall":
            query = args.get("query")
            if not query or not isinstance(query, str):
                return ToolOutput(success=False, error="/recall requires a query string.")
            results = self.collection.query(query_texts=[query], n_results=3)
            docs = results.get("documents", [[]])[0]
            if not docs:
                return ToolOutput(success=True, message="No relevant memory found.")
            return ToolOutput(success=True, message="\n".join(docs))
        else:
            return ToolOutput(success=False, error=f"Unsupported operation: {op}")

# Register the tool globally
ToolRegistry.register("memory", ChromaMemoryTool()) 