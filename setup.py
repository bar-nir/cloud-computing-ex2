import boto3
import uuid
import os
import requests

postfix = str(uuid.uuid4())
region = 'us-east-1'
ami_id = 'ami-042e8287309f5df03'
instance_type = 't2.micro'
key_name = 'cloud-ex1-' + postfix
security_group_name = 'flask-app-sg-ex1-' + postfix
flask_app_path = '/cloud-computing-ex1'
flask_app_port = 5000
ssh_port = 22

url = "https://api.ipify.org?format=json"
response = requests.get(url)
ip_address = response.json()["ip"]


ec2 = boto3.client('ec2', region_name=region)


response = ec2.create_key_pair(KeyName=key_name)
key_material = response['KeyMaterial']
with open(f'{key_name}.pem', 'w') as f:
    f.write(key_material)
os.chmod(f'{key_name}.pem', 0o400)


response = ec2.create_security_group(
    Description='Flask App Security Group EX1',
    GroupName=security_group_name,
)
security_group_id = response['GroupId']


ec2.authorize_security_group_ingress(
    GroupId=security_group_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': flask_app_port,
            'ToPort': flask_app_port,
            'IpRanges': [{'CidrIp': f'{ip_address}/32'}]
        },
    ]
)


ec2.authorize_security_group_ingress(
    GroupId=security_group_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': ssh_port,
            'ToPort': ssh_port,
            'IpRanges': [{'CidrIp': f'{ip_address}/32'}]
        },
    ]
)


response = ec2.run_instances(
    ImageId=ami_id,
    InstanceType=instance_type,
    KeyName=key_name,
    SecurityGroupIds=[security_group_id],
    MinCount=1,
    MaxCount=1,
    UserData=f'''#!/bin/bash
sudo apt update -y
sudo apt install -y python3
sudo apt install -y python3-pip
sudo apt install -y git
git clone https://github.com/bar-nir/cloud-computing-ex1.git
cd {flask_app_path}
sudo chmod 777 app.py
sudo pip3 install -r requirements.txt
sudo python3 app.py
''',
)
instance_id = response['Instances'][0]['InstanceId']
print(f'Launching instance {instance_id}...')


waiter = ec2.get_waiter('instance_status_ok')
waiter.wait(InstanceIds=[instance_id])
print(f'Instance {instance_id} is running.')


response = ec2.describe_instances(InstanceIds=[instance_id])
public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']

with open('parameters.txt', 'w') as f:
    f.write(f'{key_name}\n')
    f.write(f'{security_group_name}\n')
    f.write(f'{instance_id}\n')


url = f'http://{public_ip}:{flask_app_port}/entry?plate=123-123-123&parkingLot=123'
print(f'sending post request to url: {url}')
response = requests.post(url)
print(response.status_code, response.content)

url = f'http://{public_ip}:{flask_app_port}/exit?ticketId=1'
print(f'sending post request to url: {url}')
response = requests.post(url)
print(response.status_code, response.content)