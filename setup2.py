import boto3
import requests

print("Starting deplyomant")

url = "https://api.ipify.org?format=json"
response = requests.get(url)
ip_address = response.json()["ip"]

print(f'my ip: {ip_address}')

cloudformation = boto3.client('cloudformation')
ec2 = boto3.client('ec2')

stack_name = 'MyStack'
template_file = 'deploymant.yaml'
my_ip = ip_address

with open(template_file, 'r') as file:
    template_body = file.read()

print("creating stack request")

response = cloudformation.create_stack(
    StackName=stack_name,
    TemplateBody=template_body,
    Parameters=[
        {
            'ParameterKey': 'MyIP',
            'ParameterValue': my_ip,
        },
    ],
)

print(response)

print('Waiting for stack creation to complete...')
waiter = cloudformation.get_waiter('stack_create_complete')
waiter.wait(StackName=stack_name)
print('Stack creation complete.')

response = cloudformation.describe_stacks(StackName=stack_name)
stack_outputs = response['Stacks'][0]['Outputs']

print('Public IPs of EC2 instances:', stack_outputs)

public_ips = [output['OutputValue']
              for output in stack_outputs if output['OutputKey'] == 'WebsiteURL']

print('Public IPs of EC2 instances:', public_ips)
