class GraphAPIError(Exception):
    pass


class RateLimitError(GraphAPIError):
    pass


class NotFoundError(GraphAPIError):
    pass


class AuthenticationError(GraphAPIError):
    pass


class ValidationError(GraphAPIError):
    pass
