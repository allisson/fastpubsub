"""Custom exception classes for fastpubsub application."""


class NotFoundError(Exception):
    """Exception raised when a requested resource is not found.

    This exception is typically used when trying to access or manipulate
    database entities that don't exist.
    """

    pass


class AlreadyExistsError(Exception):
    """Exception raised when attempting to create a resource that already exists.

    This exception is used for unique constraint violations where
    a duplicate resource creation is attempted.
    """

    pass


class ServiceUnavailable(Exception):
    """Exception raised when a service operation cannot be completed.

    This exception is used when external dependencies or services
    are not available or operations fail unexpectedly.
    """

    pass


class InvalidClient(Exception):
    """Exception raised when a client is not authorized or valid.

    This exception is used when client authentication fails or
    a client lacks necessary permissions.
    """

    pass


class InvalidClientToken(Exception):
    """Exception raised when a client token is invalid or expired.

    This exception is used when JWT token validation fails or
    the token format/claims are incorrect.
    """

    pass
