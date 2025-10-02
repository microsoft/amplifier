#!/usr/bin/env python3
"""
DAG Navigator Module - Reconstruct conversation branches from the DAG structure.

This module handles DAG traversal algorithms to extract conversation branches
and sidechains from the session data.
"""

import logging
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from dag_loader import SessionData

logger = logging.getLogger(__name__)


@dataclass
class Branch:
    """Represents a conversation branch in the DAG."""

    branch_id: str
    messages: list[str] = field(default_factory=list)
    is_sidechain: bool = False
    parent_branch: str | None = None
    child_branches: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, uuid: str):
        """Add a message UUID to this branch."""
        self.messages.append(uuid)

    def count_messages(self) -> int:
        """Count messages in this branch."""
        return len(self.messages)


@dataclass
class ConversationTree:
    """Represents the entire conversation tree with all branches."""

    main_branch: Branch | None = None
    branches: dict[str, Branch] = field(default_factory=dict)
    sidechain_roots: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_branch(self, branch: Branch):
        """Add a branch to the tree."""
        self.branches[branch.branch_id] = branch
        if not branch.is_sidechain and self.main_branch is None:
            self.main_branch = branch

    def get_branch(self, branch_id: str) -> Branch | None:
        """Get a branch by ID."""
        return self.branches.get(branch_id)

    def count_branches(self) -> int:
        """Count total branches."""
        return len(self.branches)

    def count_sidechains(self) -> int:
        """Count sidechain branches."""
        return sum(1 for b in self.branches.values() if b.is_sidechain)


class DAGNavigator:
    """Navigate the DAG to extract conversation branches and sidechains."""

    def __init__(self, session_data: SessionData):
        self.session_data = session_data
        self.tree = ConversationTree()
        self.visited_messages: set[str] = set()
        self.branch_counter = 0

    def build_conversation_tree(self) -> ConversationTree:
        """Build the complete conversation tree from the DAG.

        Returns:
            ConversationTree containing all branches and sidechains
        """
        logger.info("Building conversation tree from DAG")

        # Process root messages
        roots = self.session_data.get_roots()
        if not roots:
            logger.warning("No root messages found in session")
            return self.tree

        # Process each root (could be multiple in complex sessions)
        for root_uuid in roots:
            root_msg = self.session_data.get_message(root_uuid)
            if root_msg and root_msg.is_sidechain:
                # It's a sidechain root
                self._process_sidechain_root(root_uuid)
            else:
                # It's a main conversation root
                self._process_main_root(root_uuid)

        logger.info(f"Built tree with {self.tree.count_branches()} branches")
        if self.tree.count_sidechains() > 0:
            logger.info(f"Found {self.tree.count_sidechains()} sidechains")

        return self.tree

    def _process_main_root(self, root_uuid: str):
        """Process a root message from the main conversation."""
        # Create the main branch
        branch = self._create_branch(is_sidechain=False)
        self.tree.main_branch = branch

        # Traverse from root
        self._traverse_branch(root_uuid, branch)

    def _process_sidechain_root(self, root_uuid: str):
        """Process a root message from a sidechain."""
        # Create a sidechain branch
        branch = self._create_branch(is_sidechain=True)
        self.tree.sidechain_roots.append(root_uuid)

        # Traverse the sidechain
        self._traverse_branch(root_uuid, branch)

    def _traverse_branch(self, start_uuid: str, branch: Branch):
        """Traverse a branch starting from a message.

        This handles both linear paths and branch points.
        """
        current_uuid = start_uuid

        while current_uuid:
            # Skip if already visited
            if current_uuid in self.visited_messages:
                break

            # Mark as visited and add to branch
            self.visited_messages.add(current_uuid)
            branch.add_message(current_uuid)

            # Get children
            children = self.session_data.get_children(current_uuid)

            if len(children) == 0:
                # End of branch
                break
            if len(children) == 1:
                # Linear continuation
                current_uuid = children[0]
            else:
                # Branch point - multiple children
                self._handle_branch_point(current_uuid, children, branch)
                break

    def _handle_branch_point(self, parent_uuid: str, children: list[str], parent_branch: Branch):
        """Handle a message with multiple children (branch point)."""
        logger.debug(f"Branch point at {parent_uuid} with {len(children)} children")

        for child_uuid in children:
            if child_uuid in self.visited_messages:
                continue

            # Check if it's a sidechain
            child_msg = self.session_data.get_message(child_uuid)
            is_sidechain = child_msg.is_sidechain if child_msg else False

            # Create new branch
            new_branch = self._create_branch(is_sidechain=is_sidechain)
            new_branch.parent_branch = parent_branch.branch_id
            parent_branch.child_branches.append(new_branch.branch_id)

            # Traverse the new branch
            self._traverse_branch(child_uuid, new_branch)

    def _create_branch(self, is_sidechain: bool = False) -> Branch:
        """Create a new branch and add it to the tree."""
        self.branch_counter += 1
        branch_id = f"branch_{self.branch_counter}"
        if is_sidechain:
            branch_id = f"sidechain_{self.branch_counter}"

        branch = Branch(branch_id=branch_id, is_sidechain=is_sidechain)
        self.tree.add_branch(branch)
        return branch

    def get_linear_flow(self) -> list[str]:
        """Get a simple linear flow of messages (ignoring branches).

        This provides a simplified view by following the 'main' path.

        Returns:
            List of message UUIDs in linear order
        """
        if not self.tree.main_branch:
            # Fallback to chronological order
            return self._get_chronological_flow()

        flow = []

        def follow_main_path(branch: Branch):
            """Follow the main path through branches."""
            for msg_uuid in branch.messages:
                flow.append(msg_uuid)

            # Follow first child branch if exists (main path)
            if branch.child_branches:
                first_child = self.tree.get_branch(branch.child_branches[0])
                if first_child and not first_child.is_sidechain:
                    follow_main_path(first_child)

        follow_main_path(self.tree.main_branch)
        return flow

    def _get_chronological_flow(self) -> list[str]:
        """Get messages in chronological order based on line numbers."""
        messages = list(self.session_data.messages.values())
        messages.sort(key=lambda m: m.line_number)
        return [m.uuid for m in messages]

    def get_all_branches(self) -> list[Branch]:
        """Get all branches in the conversation tree."""
        return list(self.tree.branches.values())

    def get_sidechains(self) -> list[Branch]:
        """Get all sidechain branches."""
        return [b for b in self.tree.branches.values() if b.is_sidechain]

    def find_branch_for_message(self, message_uuid: str) -> Branch | None:
        """Find which branch contains a specific message."""
        for branch in self.tree.branches.values():
            if message_uuid in branch.messages:
                return branch
        return None

    def get_branch_hierarchy(self) -> dict[str, list[str]]:
        """Get the hierarchy of branches (parent -> children mapping)."""
        hierarchy = {}
        for branch in self.tree.branches.values():
            if branch.parent_branch:
                parent = branch.parent_branch
                if parent not in hierarchy:
                    hierarchy[parent] = []
                hierarchy[parent].append(branch.branch_id)
        return hierarchy
