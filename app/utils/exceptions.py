from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, resource: str, identifier: str | None = None):
        detail = {"status": "error", "message": "", "identifier": identifier}
        if identifier:
            detail["message"] = f"{resource} with identifier '{identifier}' not found"
        else:
            detail["message"] = f"{resource} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


class ConflictException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)


class UnauthorizedException(HTTPException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)
