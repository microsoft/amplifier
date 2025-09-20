"""Unit tests for GitHub API client."""

import base64
from unittest.mock import AsyncMock
from unittest.mock import patch

import httpx
import pytest

from amplifier.cli.core.github import GitHubClient


class TestGitHubClient:
    """Test GitHub API client functionality."""

    @pytest.fixture
    def client(self):
        """Create GitHub client with test token."""
        return GitHubClient(token="test_token_123")

    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client."""
        mock = AsyncMock()
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock(return_value=None)
        return mock

    @pytest.mark.asyncio
    async def test_fetch_resource_success(self, client):
        """Test successful resource fetch from GitHub."""
        # Arrange
        test_content = "# Test Agent\n\nThis is test content"
        encoded_content = base64.b64encode(test_content.encode()).decode()

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "sha": "abc123def456",
            "size": len(test_content),
            "encoding": "base64",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            content, sha = await client.fetch_resource("agents", "test-agent", ref="main")

            # Assert
            assert content == test_content
            assert sha == "abc123def456"
            mock_client.get.assert_called_once()

            # Verify correct URL and params
            call_args = mock_client.get.call_args
            assert ".claude/agents/test-agent.md" in call_args[0][0]
            assert call_args[1]["params"]["ref"] == "main"

    @pytest.mark.asyncio
    async def test_fetch_resource_not_found(self, client):
        """Test resource not found returns None."""
        # Arrange
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            content, sha = await client.fetch_resource("agents", "nonexistent")

            # Assert
            assert content is None
            assert sha is None

    @pytest.mark.asyncio
    async def test_fetch_resource_timeout(self, client):
        """Test timeout handling returns None gracefully."""
        # Arrange
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            content, sha = await client.fetch_resource("agents", "test-agent")

            # Assert
            assert content is None
            assert sha is None

    @pytest.mark.asyncio
    async def test_fetch_resource_network_error(self, client):
        """Test network error handling."""
        # Arrange
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.NetworkError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            content, sha = await client.fetch_resource("tools", "test-tool")

            # Assert
            assert content is None
            assert sha is None

    @pytest.mark.asyncio
    async def test_fetch_resource_rate_limited(self, client):
        """Test rate limit handling."""
        # Arrange
        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1234567890"}
        mock_response.text = "Rate limit exceeded"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            content, sha = await client.fetch_resource("agents", "test")

            # Assert
            assert content is None
            assert sha is None

    @pytest.mark.asyncio
    async def test_list_resources_success(self, client):
        """Test listing resources filters correctly."""
        # Arrange
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "agent1.md", "type": "file", "path": ".claude/agents/agent1.md"},
            {"name": "agent2.md", "type": "file", "path": ".claude/agents/agent2.md"},
            {"name": "README.md", "type": "file", "path": ".claude/agents/README.md"},
            {"name": ".gitkeep", "type": "file", "path": ".claude/agents/.gitkeep"},
            {"name": "test.txt", "type": "file", "path": ".claude/agents/test.txt"},
            {"name": "subdir", "type": "dir", "path": ".claude/agents/subdir"},
        ]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            resources = await client.list_resources("agents", ref="main")

            # Assert
            assert "agent1" in resources
            assert "agent2" in resources
            assert "README" not in resources  # Should be filtered
            assert ".gitkeep" not in resources  # Should be filtered
            assert "test" not in resources  # Wrong extension
            assert "subdir" not in resources  # Directory

    @pytest.mark.asyncio
    async def test_list_resources_empty(self, client):
        """Test listing empty directory."""
        # Arrange
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            resources = await client.list_resources("tools")

            # Assert
            assert resources == []

    @pytest.mark.asyncio
    async def test_list_resources_not_found(self, client):
        """Test listing non-existent directory."""
        # Arrange
        mock_response = AsyncMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            resources = await client.list_resources("invalid-type")

            # Assert
            assert resources == []

    @pytest.mark.asyncio
    async def test_fetch_with_different_refs(self, client):
        """Test fetching from different git refs."""
        # Arrange
        test_content = "# Content from branch"
        encoded = base64.b64encode(test_content.encode()).decode()

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": encoded, "sha": "branch-sha"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act - test with branch
            content, sha = await client.fetch_resource("agents", "test", ref="dev-branch")

            # Assert
            assert content == test_content
            assert sha == "branch-sha"

            # Verify ref was passed correctly
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["ref"] == "dev-branch"

    def test_client_headers_with_token(self):
        """Test client sets correct headers with token."""
        # Arrange & Act
        client = GitHubClient(token="secret_token")

        # Assert
        assert client.headers["Authorization"] == "Bearer secret_token"
        assert client.headers["Accept"] == "application/vnd.github.v3+json"
        assert client.headers["User-Agent"] == "amplifier-cli-v3"

    def test_client_headers_without_token(self):
        """Test client headers without token."""
        # Arrange & Act
        client = GitHubClient()

        # Assert
        assert "Authorization" not in client.headers
        assert client.headers["Accept"] == "application/vnd.github.v3+json"
