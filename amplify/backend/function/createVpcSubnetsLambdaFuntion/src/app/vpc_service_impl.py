import uuid
import time
from .vpc_service import VpcService
import decimal
from boto3.dynamodb.conditions import Key

class VpcServiceImpl(VpcService):
    def create_vpc(self, ec2, vpc_cidr, vpc_name):
        # Create the VPC
        vpc_response = ec2.create_vpc(CidrBlock=vpc_cidr)
        vpc_id = vpc_response['Vpc']['VpcId']
        print(f"Created VPC: {vpc_id}")

        # Wait until the VPC is available
        waiter = ec2.get_waiter('vpc_available')
        waiter.wait(VpcIds=[vpc_id])

        # Tag the VPC with the specified name
        ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': vpc_name}])
        return vpc_id

    def create_subnet(self, ec2, vpc_id, subnet_info):
        subnet_response = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=subnet_info['cidr'],
            AvailabilityZone=subnet_info['availabilityZone']
        )
        subnet_id = subnet_response['Subnet']['SubnetId']
        print(f"Created Subnet: {subnet_id} in {subnet_info['availabilityZone']}")

        # Tag the subnet with its given name
        ec2.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': subnet_info['subnetName']}])
        return {
            'subnet_id': subnet_id,
            'name': subnet_info['subnetName'],
            'cidr': subnet_info['cidr'],
            'availability_zone': subnet_info['availabilityZone']
        }

    def delete_vpc_and_subnets(self, ec2, vpc_id):
        # Retrieve all subnets in the VPC
        response = ec2.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        subnets = response.get('Subnets', [])
        
        # Delete each subnet
        for subnet in subnets:
            subnet_id = subnet['SubnetId']
            print(f"Deleting subnet: {subnet_id}")
            ec2.delete_subnet(SubnetId=subnet_id)
        
        # Delete the VPC itself
        print(f"Deleting VPC: {vpc_id}")
        ec2.delete_vpc(VpcId=vpc_id)
        print("VPC and all its subnets have been deleted.")

    def record_vpc_details(self, dynamodb, table_name, user_id, vpc_name, vpc_id, vpc_cidr, subnets_details):
        table = dynamodb.Table(table_name)
        record = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'vpc_name': vpc_name,
            'creation_datetime': int(time.time()),
            'vpc_id': vpc_id,
            'vpc_cidr': vpc_cidr,
            'subnets': subnets_details
        }
        table.put_item(Item=record)
        print("Record inserted into DynamoDB")
        return record['id']

    def convert_decimals(self, obj):
        """
        Recursively convert Decimal objects to int or float.
        """
        if isinstance(obj, list):
            return [self.convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self.convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, decimal.Decimal):
            # If the decimal is equivalent to an integer, return it as int
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        else:
            return obj

    def query_vpc_record(self, table, vpc_name):
        response = table.query(
            IndexName='vpc_name-creation_datetime-index',
            KeyConditionExpression=Key('vpc_name').eq(vpc_name)
        )
        items = response.get('Items', [])
        print("Query result from DynamoDB:",items)
        # Convert Decimal objects in the result
        items = self.convert_decimals(items)
        return response.get('Items', [])