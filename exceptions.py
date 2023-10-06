class StatusCodeException(Exception):
    """Status code other than 200."""

    pass


class EmptyResponseApiException(Exception):
    """API response does not contain expected key."""

    pass


class EnvironmentVariableError(Exception):
    """A required environment variable is missing."""

    pass


class EndpointAvailabilityError(Exception):
    """The request to the API service endpoint is not available."""

    pass
