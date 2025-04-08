import json
import traceback
import os
from .errors import ClientError
from .error_messages import get_error_message
from .vpc_service_impl import VpcServiceImpl

def handle_exception(func):
    def wrapper(event, context):
        try:
            return func(event, context)
        except ClientError as ce:
            # Return a user-friendly error for client-side issues.
            return {
                'statusCode': ce.status_code,
                'body': json.dumps({'error': ce.message})
            }
        except Exception as e:
            # Log detailed internal error for debugging.
            print("Internal Server Error:", traceback.format_exc())
            # Extract the exception reason as a string.
            exception_reason = str(e)
            # Retrieve the friendly error message with the exception reason replacing {message}.
            error_message = get_error_message("INTERNAL_SERVER_ERROR", message=exception_reason)
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': error_message
                })
            }
    return wrapper
