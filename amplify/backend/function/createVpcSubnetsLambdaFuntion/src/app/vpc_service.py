class VpcService:
    def create_vpc(self, ec2, vpc_cidr, vpc_name):
        raise NotImplementedError("Subclasses must implement this method")
    
    def create_subnet(self, ec2, vpc_id, subnet_info):
        raise NotImplementedError("Subclasses must implement this method")
    
    def record_vpc_details(self, dynamodb, table_name, user_id, vpc_name, vpc_id, subnets_details):
        raise NotImplementedError("Subclasses must implement this method")
    
    def query_vpc_record(self, table, vpc_name):
        raise NotImplementedError("Subclasses must implement this method")
