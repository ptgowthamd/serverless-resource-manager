import json
import traceback
import os
import botocore
from .errors import ClientError
from .error_messages import get_error_message
from .vpc_service_impl import VpcServiceImpl

def handle_exception(func):
    def wrapper(event, context):
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        }
        try:
            return func(event, context)
        except botocore.exceptions.ClientError as aws_err:

            code = aws_err.response['Error']['Code']
            if code == "InvalidSubnet.Conflict":
                # Pull out what we stashed earlier
                vpc_id = getattr(context, "vpc_id", None)
                ec2    = getattr(context, "ec2_client", None)

                if vpc_id and ec2:
                    try:
                        # central cleanup
                        VpcServiceImpl().delete_vpc_and_subnets(ec2, vpc_id)
                    except Exception as cleanup_err:
                        print("Cleanup failed:", cleanup_err)

                return {
                  'statusCode': 409,
                  'headers': cors_headers,
                  'body': json.dumps({
                    "error": "Subnet CIDR conflict: overlaps an existing subnet"
                  })
                }
            elif code == "VpcLimitExceeded":
                status  = 429
                message = "VPC limit exceeded: maximum number of VPCs reached."
            else:
                status  = 500
                # use your friendly‐error templating for all other AWS errors
                message = get_error_message("INTERNAL_SERVER_ERROR",message=str(aws_err))
            return {
                'statusCode': status,
                'headers':    cors_headers,
                'body':       json.dumps({'error': message})
            }

        except ClientError as ce:
            # Return a user-friendly error for client-side issues.
            return {
                'statusCode': ce.status_code,
                'headers': cors_headers,
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
                'headers': cors_headers,
                'body': json.dumps({
                    'error': error_message
                })
            }
    return wrapper
