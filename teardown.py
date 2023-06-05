import boto3
import os

# Replace these with the values from the environment variables
region = 'us-east-1'

# Load values from file
with open('parameters.txt', 'r') as f:
    key_name = f.readline().strip()
    security_group_name = f.readline().strip()
    instance_id = f.readline().strip()

# Create a new EC2 client
ec2 = boto3.client('ec2', region_name=region)

# Terminate the EC2 instance
ec2.terminate_instances(InstanceIds=[instance_id])

# Wait for the instance to terminate
waiter = ec2.get_waiter('instance_terminated')
waiter.wait(InstanceIds=[instance_id])
print(f'Terminated instance {instance_id}.')

# Delete the security group
response = ec2.describe_security_groups(GroupNames=[security_group_name])
security_group_id = response['SecurityGroups'][0]['GroupId']
ec2.delete_security_group(GroupId=security_group_id)
print(f'Deleted security group {security_group_id}.')

# Delete the key pair and the .pem file
response = ec2.delete_key_pair(KeyName=key_name)
print(f'Deleted key pair {key_name}.')
os.remove(f'{key_name}.pem')
print(f'Deleted {key_name}.pem file.')

if os.path.exists('parameters.txt'):
    os.remove('parameters.txt')
    print('parameters file deleted successfully')
else:
    print('parameters the file does not exist')