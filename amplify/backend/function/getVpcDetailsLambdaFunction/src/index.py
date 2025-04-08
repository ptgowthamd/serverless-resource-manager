import os
import time
import uuid
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key

# Custom JSON encoder to handle Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            # Optionally, you can return float(o) or str(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)

# ----------------------- Helper Functions -----------------------

def query_vpc_record(table, vpc_name):
    """
    Queries the DynamoDB table using the vpc_name as the partition key.
    Returns the list of items found.
    """
    response = table.query(
        IndexName='vpc_name-creation_datetime-index',
        KeyConditionExpression=Key('vpc_name').eq(vpc_name)
    )
    print("Query result from DynamoDB:", response.get('Items', []))
    return response.get('Items', [])

# ----------------------- Lambda Handler -----------------------

def handler(event, context):
    try:
        print(json.dumps(event))
        vpc_name = event['pathParameters']['name']
        
        # Retrieve DynamoDB table name and region from environment variables
        table_name = os.environ.get('STORAGE_USERVPCSUBNETDETAILS_NAME')
        region = os.environ.get('REGION')
        
        # Create a DynamoDB resource in its specified region
        dynamodb = boto3.resource('dynamodb', region_name=region)

        # Query the record using the vpc_name
        table = dynamodb.Table(table_name)
        items = query_vpc_record(table, vpc_name)
        
        message = 'VPC and subnet details for given vpc_name'
        if len(items) == 0:
            message = 'No record found for given vpc_name'

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': message,
                'vpc_subnets_details': items
            }, cls=DecimalEncoder)
        }
    except Exception as error:
        # Log the exception details
        print(f"Error: {error}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(error)
            })
        }