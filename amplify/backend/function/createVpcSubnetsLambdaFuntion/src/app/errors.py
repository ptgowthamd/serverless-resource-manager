from .error_messages import get_error_message

class ClientError(Exception):
    """Exception raised for client-side issues (e.g., invalid input)."""
    def __init__(self, error_name, status_code=400, **kwargs):
        self.error_name = error_name
        self.status_code = status_code
        self.message = get_error_message(error_name, **kwargs)
        super().__init__(self.message)
