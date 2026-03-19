# ============================================================
# config.py — The settings file for ONE node
#
# WHAT IS THIS FILE FOR?
# Every node needs to know:
#   - Who am I? (my ID, my port)
#   - Who are my peers? (other nodes I need to talk to)
#   - What are my quorum rules? (W and R values)
#
# Instead of hardcoding these values, we load them from
# environment variables. This way, the SAME codebase runs
# on all 3 nodes — just with different .env values.
#
# Real world example: Same Docker image, 3 different configs.
# ============================================================

# BaseSettings is pydantic's way of reading from .env files
# It auto-reads env vars and validates their types for you
from pydantic_settings import BaseSettings

# Field lets us rename env vars to python-friendly names
# e.g. env var NODE_ID becomes node_id in Python
from pydantic import Field

# For type hints
from typing import Dict


# ============================================================
# This class holds ALL config for the running node.
# pydantic will automatically read from your .env file.
# ============================================================
class Settings(BaseSettings):

    # --- Who am I? ---

    # The unique name of THIS node (e.g. "node1", "node2")
    # alias="NODE_ID" means it reads from the NODE_ID env var
    node_id: str = Field(default="node1", alias="NODE_ID")

    # The host this node listens on
    # 0.0.0.0 means "accept connections from anywhere"
    node_host: str = Field(default="0.0.0.0", alias="NODE_HOST")

    # The port this node listens on (8001, 8002, or 8003)
    node_port: int = Field(default=8001, alias="NODE_PORT")

    # --- Quorum settings ---
    # Remember: W + R > N must always be true

    # N — total number of nodes in the cluster
    total_nodes: int = Field(default=3, alias="TOTAL_NODES")

    # W — how many nodes must confirm a WRITE before success
    write_quorum: int = Field(default=2, alias="WRITE_QUORUM")

    # R — how many nodes must respond to a READ
    read_quorum: int = Field(default=2, alias="READ_QUORUM")

    # --- Peer information ---

    # Raw string from env var, looks like:
    # "node1=localhost:8001,node2=localhost:8002,node3=localhost:8003"
    # We parse this into a usable dict in the peers property below
    peer_nodes_raw: str = Field(
        default="node1=localhost:8001,node2=localhost:8002,node3=localhost:8003",
        alias="PEER_NODES"
    )

    # ============================================================
    # @property means this is computed, not stored
    # Call it like settings.peers — no parentheses needed
    # ============================================================
    @property
    def peers(self) -> Dict[str, str]:
        """
        Parses peer_nodes_raw into a dict.

        Input:  "node1=localhost:8001,node2=localhost:8002"
        Output: {"node1": "http://localhost:8001", "node2": "http://localhost:8002"}
        """
        result = {}

        # Split by comma to get each "nodeX=host:port" entry
        for entry in self.peer_nodes_raw.split(","):

            # Split by "=" to separate the node id from the address
            node_id, address = entry.strip().split("=")

            # Store as full URL so we can use it directly in HTTP calls
            result[node_id.strip()] = f"http://{address.strip()}"

        return result

    @property
    def peer_urls(self) -> list[str]:
        """
        Returns only the URLs of OTHER nodes (not self).

        Why exclude self? Because when we replicate, we already
        wrote locally — we only need to tell the OTHER nodes.
        """
        return [
            url
            for node_id, url in self.peers.items()
            if node_id != self.node_id  # skip ourselves
        ]

    class Config:
        # Tell pydantic to look for a .env file
        env_file = ".env"

        # Allow using either the alias (NODE_ID) or field name (node_id)
        populate_by_name = True


# ============================================================
# Create ONE shared instance of settings.
# Every other file imports THIS object — not the class.
#
# Usage in other files:
#   from src.config import settings
#   print(settings.node_id)   # "node1"
#   print(settings.peer_urls) # ["http://localhost:8002", ...]
# ============================================================
settings = Settings()