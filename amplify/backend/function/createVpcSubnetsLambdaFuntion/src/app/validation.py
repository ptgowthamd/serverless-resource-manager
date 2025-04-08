import ipaddress
from .errors import ClientError
import os
from .vpc_service_impl import VpcServiceImpl

# List of valid AWS regions (extend as needed)
VALID_REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "af-south-1", "ap-east-1", "ap-south-1", "ap-northeast-1",
    "ap-northeast-2", "ap-northeast-3", "ap-southeast-1",
    "ap-southeast-2", "ca-central-1", "cn-north-1", "cn-northwest-1",
    "eu-central-1", "eu-west-1", "eu-west-2", "eu-west-3",
    "eu-north-1", "me-south-1", "sa-east-1"
]

vpc_service = VpcServiceImpl()

def validate_request_body(data):
    """
    Validates the input request body for creating a VPC and its subnets.
    Expected format:
    {
      "vpcName": "TestVPC",                     // required
      "region": "ap-south-1",                    // required and must be a valid region
      "cidr": "10.0.0.0/16",                     // required, valid CIDR block
      "subnets": [                             // required and cannot be empty
          {
            "subnetName": "subnet-1",            // required
            "cidr": "10.0.0.0/26",               // required, must be within VPC CIDR block
            "availabilityZone": "ap-south-1a"    // required, must start with the given region
          },
          {
            "subnetName": "subnet-2",
            "cidr": "10.0.0.0/26",
            "availabilityZone": "ap-south-1b"
          }
      ]
    }
    Returns a dictionary with validated values.
    Raises ClientError with proper error messages if any check fails.
    """
    # Check for required top-level keys
    required_fields = ["vpcName", "region", "cidr", "subnets"]
    for field in required_fields:
        if field not in data:
            raise ClientError("FIELD_REQUIRED", field=field)
    
    vpc_name = data["vpcName"]
    region = data["region"]
    vpc_cidr = data["cidr"]
    subnets = data["subnets"]

    # Validate vpcName
    if not isinstance(vpc_name, str) or not vpc_name.strip():
        raise ClientError("INVALID_VPC_NAME")
    
    # Validate region is a string and is in the allowed regions list
    if not isinstance(region, str) or region not in VALID_REGIONS:
        raise ClientError("INVALID_REGION", region=region, allowed_regions=", ".join(VALID_REGIONS))
    
    # Validate VPC CIDR
    try:
        vpc_network = ipaddress.ip_network(vpc_cidr)
    except ValueError:
        raise ClientError("INVALID_CIDR", cidr=vpc_cidr)
    
    # Validate that subnets is a non-empty list
    if not isinstance(subnets, list) or not subnets:
        raise ClientError("EMPTY_SUBNETS")
    
    validated_subnets = []
    for idx, subnet in enumerate(subnets, start=1):
        # Check required fields in each subnet
        for field in ["subnetName", "cidr", "availabilityZone"]:
            if field not in subnet:
                raise ClientError("FIELD_REQUIRED", field=f"{field} in subnet #{idx}")
        
        subnet_name = subnet["subnetName"]
        subnet_cidr = subnet["cidr"]
        availability_zone = subnet["availabilityZone"]

        # Validate subnetName is a non-empty string
        if not isinstance(subnet_name, str) or not subnet_name.strip():
            raise ClientError("INVALID_SUBNET_NAME", index=idx)
        
        # Validate subnet CIDR block
        try:
            subnet_network = ipaddress.ip_network(subnet_cidr)
        except ValueError:
            raise ClientError("INVALID_SUBNET_CIDR", cidr=subnet_cidr, index=idx)
        
        # Check that the subnet CIDR is a subset of the VPC CIDR block
        if not subnet_network.subnet_of(vpc_network):
            raise ClientError("SUBNET_NOT_IN_VPC", subnet_cidr=subnet_cidr, index=idx, vpc_cidr=vpc_cidr)
        
        # Validate availabilityZone: it must start with the provided region string
        if not isinstance(availability_zone, str) or not availability_zone.startswith(region) or not len(region)<len(availability_zone):
            raise ClientError("INVALID_AVAILABILITY_ZONE", az=availability_zone, index=idx, region=region)
        
        validated_subnets.append({
            "subnetName": subnet_name,
            "cidr": subnet_cidr,
            "availabilityZone": availability_zone
        })
    
    # Return the validated and normalized data
    return {
        "vpcName": vpc_name,
        "region": region,
        "cidr": vpc_cidr,
        "subnets": validated_subnets
    }

def extract_user_sub(event):
    """
    Extracts the 'sub' value from event['requestContext']['authorizer']['claims'].
    
    Raises:
        ClientError: If the 'sub' claim is missing.
    
    Returns:
        str: The user identifier from the event claims.
    """
    try:
        user_sub = event["requestContext"]["authorizer"]["claims"]["sub"]
        if not user_sub:
            raise KeyError("sub claim is empty")
        return user_sub
    except KeyError:
        raise ClientError("AUTH_USER_MISSING", message="User identifier (sub) is missing from the request claims.")
    
def validate_env(var_name):
    value = os.environ.get(var_name)
    if not value:
        raise ClientError("ENV_MISSING", var_name=var_name)
    return value

def validate_existance_vpc_name(table, vpc_name):
    if len(vpc_service.query_vpc_record(table, vpc_name)) != 0:
        raise ClientError("VPC_EXISTED", vpc_name=vpc_name)