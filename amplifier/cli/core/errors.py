"""Custom exception hierarchy for Amplifier CLI."""

import click


class AmplifierCLIError(click.ClickException):
    """Base exception for all Amplifier CLI errors.

    This provides consistent error formatting and exit codes.
    """

    def __init__(self, message: str, hint: str | None = None):
        """Initialize the exception.

        Args:
            message: The error message to display
            hint: Optional hint to help resolve the error
        """
        super().__init__(message)
        self.hint = hint

    def format_message(self) -> str:
        """Format the error message with optional hint.

        Returns:
            Formatted error message
        """
        msg = self.message
        if self.hint:
            msg += f"\n\nHint: {self.hint}"
        return msg

    def show(self, file=None) -> None:
        """Show the exception message."""
        click.echo(f"Error: {self.format_message()}", err=True)


class NotInitializedError(AmplifierCLIError):
    """Raised when project is not initialized."""

    def __init__(self, message: str | None = None):
        """Initialize the not initialized error."""
        if message is None:
            message = "This project has not been initialized with Amplifier CLI."
        hint = "Run 'amplifier init' to initialize the project first."
        super().__init__(message, hint=hint)


class ResourceNotFoundError(AmplifierCLIError):
    """Raised when a requested resource doesn't exist."""

    def __init__(self, resource_type: str, resource_name: str, available: list[str] | None = None):
        """Initialize the resource not found error.

        Args:
            resource_type: Type of resource (agents, tools, etc.)
            resource_name: Name of the resource that wasn't found
            available: Optional list of available resources
        """
        message = f"{resource_type.capitalize()} '{resource_name}' not found."
        hint = None
        if available:
            # Show up to 5 similar resources
            suggestions = available[:5]
            hint = f"Available {resource_type}: {', '.join(suggestions)}"
            if len(available) > 5:
                hint += f" (and {len(available) - 5} more)"
        super().__init__(message, hint=hint)


class GitHubAPIError(AmplifierCLIError):
    """Raised when GitHub API operations fail."""

    def __init__(self, message: str, status_code: int | None = None):
        """Initialize the GitHub API error.

        Args:
            message: Error message
            status_code: Optional HTTP status code from GitHub
        """
        hint = None
        if status_code == 403:
            hint = (
                "You may have exceeded the GitHub API rate limit. "
                "Try again in a few minutes or provide a GitHub token "
                "in the GITHUB_TOKEN environment variable."
            )
        elif status_code == 404:
            hint = "Check that the repository and path exist on GitHub."
        elif status_code and status_code >= 500:
            hint = "GitHub is experiencing issues. Please try again later."

        super().__init__(message, hint=hint)
        self.status_code = status_code


class ManifestError(AmplifierCLIError):
    """Raised when manifest operations fail."""

    def __init__(self, message: str, repair_possible: bool = False):
        """Initialize the manifest error.

        Args:
            message: Error message
            repair_possible: Whether the manifest can be repaired
        """
        hint = None
        if repair_possible:
            hint = "The manifest appears to be corrupted. Run 'amplifier init --repair' to attempt to fix it."
        super().__init__(message, hint=hint)
        self.repair_possible = repair_possible


class DependencyError(AmplifierCLIError):
    """Raised when resource dependencies are not met."""

    def __init__(self, resource_name: str, missing_deps: list[str]):
        """Initialize the dependency error.

        Args:
            resource_name: Name of the resource with missing dependencies
            missing_deps: List of missing dependency names
        """
        message = (
            f"Cannot install '{resource_name}' because it depends on "
            f"resources that are not installed: {', '.join(missing_deps)}"
        )
        hint = "Install the missing dependencies first or use '--with-deps' flag."
        super().__init__(message, hint=hint)
        self.missing_deps = missing_deps


class ConfigurationError(AmplifierCLIError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_file: str | None = None):
        """Initialize the configuration error.

        Args:
            message: Error message
            config_file: Optional path to the problematic config file
        """
        hint = None
        if config_file:
            hint = f"Check the configuration in: {config_file}"
        super().__init__(message, hint=hint)
        self.config_file = config_file


class NetworkError(AmplifierCLIError):
    """Raised when network operations fail."""

    def __init__(self, message: str, url: str | None = None):
        """Initialize the network error.

        Args:
            message: Error message
            url: Optional URL that failed
        """
        hint = "Check your internet connection and try again."
        if url:
            hint += f"\nFailed URL: {url}"
        super().__init__(message, hint=hint)
        self.url = url


class ValidationError(AmplifierCLIError):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: str, reason: str):
        """Initialize the validation error.

        Args:
            field: Field that failed validation
            value: The invalid value
            reason: Reason why validation failed
        """
        message = f"Invalid {field}: '{value}' - {reason}"
        super().__init__(message)
        self.field = field
        self.value = value
        self.reason = reason
