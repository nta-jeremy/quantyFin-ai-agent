from typing import Any, Optional

class BaseAppException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

class NotFoundException(BaseAppException):
    def __init__(self, message: str, code: str = "NOT_FOUND", details: Optional[Any] = None) -> None:
        super().__init__(message, code, 404, details)

class UnauthorizedException(BaseAppException):
    def __init__(self, message: str, code: str = "UNAUTHORIZED", details: Optional[Any] = None) -> None:
        super().__init__(message, code, 401, details)

class BadRequestException(BaseAppException):
    def __init__(self, message: str, code: str = "BAD_REQUEST", details: Optional[Any] = None) -> None:
        super().__init__(message, code, 400, details)

class CrawlerException(BaseAppException):
    def __init__(self, message: str, code: str = "CRAWLER_ERROR", details: Optional[Any] = None) -> None:
        super().__init__(message, code, 500, details)
