class NotFoundException(Exception):
    """Exception raised when a resource is not found"""

    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        self.message = f"{resource} with id {identifier} not found"
        super().__init__(self.message)
