"""
blockchain.py — VeriChain permissioned ledger

A minimal proof-of-work blockchain standing in for the Hyperledger Fabric
ledger specified in the System Analysis & Design baseline. Each block
records one supply-chain event (order/shipment/receipt/payment) as an
immutable, hash-linked entry, "written" by one of a fixed set of
consortium nodes — the same shape the production ledger will have,
implemented locally with no external network.
"""

import hashlib
import json
import random
import time

# Fixed set of permissioned consortium nodes allowed to write blocks.
CONSORTIUM_NODES = [
    "Node-Central-01",
    "Node-Coastal-02",
    "Node-Highland-03",
    "Node-Delta-04",
]


class Block:
    def __init__(self, index, timestamp, data, previous_hash, node=None, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.node = node
        self.nonce = nonce
        self.hash = None

    def compute_hash(self):
        block_string = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "data": self.data,
                "previous_hash": self.previous_hash,
                "node": self.node,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "node": self.node,
            "nonce": self.nonce,
            "hash": self.hash,
        }


class Ledger:
    """A single-process, in-memory permissioned chain with light proof-of-work."""

    def __init__(self, difficulty: int = 2):
        self.difficulty = difficulty
        self.chain = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis = Block(0, time.time(), {"type": "genesis"}, "0" * 64, node="Node-Central-01")
        genesis.hash = genesis.compute_hash()
        self.chain.append(genesis)

    @property
    def last_block(self):
        return self.chain[-1]

    def _proof_of_work(self, block: Block) -> str:
        block.nonce = 0
        computed_hash = block.compute_hash()
        target = "0" * self.difficulty
        while not computed_hash.startswith(target):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def record_event(self, data: dict, node: str = None) -> Block:
        """Write a supply-chain event to the ledger and return the new block."""
        node = node or random.choice(CONSORTIUM_NODES)
        block = Block(
            index=self.last_block.index + 1,
            timestamp=time.time(),
            data=data,
            previous_hash=self.last_block.hash,
            node=node,
        )
        block.hash = self._proof_of_work(block)
        self.chain.append(block)
        return block

    def is_valid(self) -> bool:
        """Verify hash linkage and proof-of-work across the whole chain."""
        target = "0" * self.difficulty
        for i in range(1, len(self.chain)):
            current, previous = self.chain[i], self.chain[i - 1]
            if current.previous_hash != previous.hash:
                return False
            if current.hash != current.compute_hash():
                return False
            if i > 0 and not current.hash.startswith(target):
                return False
        return True

    def find_block(self, order_id: str):
        for block in self.chain:
            if block.data.get("order") == order_id:
                return block
        return None
