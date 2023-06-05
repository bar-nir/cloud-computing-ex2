import random
import subprocess
import os
import boto3


def create_random_string():
    random_number = random.randint(100, 999)
    return str(random_number)


def create_clients(region):
    cloudformation = boto3.client('cloudformation', region_name=region)
    ec2 = boto3.client('ec2', region_name=region)
    return cloudformation, ec2


def create_key_pair(ec2, key_name):
    response = ec2.create_key_pair(KeyName=key_name)
    key_material = response['KeyMaterial']
    with open(f'{key_name}.pem', 'w') as f:
        f.write(key_material)
    os.chmod(f'{key_name}.pem', 0o400)


def read_template(template_file):
    with open(template_file, 'r') as file:
        template_body = file.read()
    return template_body


def create_stack(cloudformation, stack_name, template_body, key_name):
    response = cloudformation.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Parameters=[
            {
                'ParameterKey': 'MyIP',
                'ParameterValue': '0.0.0.0/0',
            },
            {
                "ParameterKey": "KeySSH",
                "ParameterValue": key_name
            }
        ],
        Capabilities=['CAPABILITY_IAM']
    )
    return response


def wait_for_stack_creation(cloudformation, stack_name):
    waiter = cloudformation.get_waiter('stack_create_complete')
    waiter.wait(StackName=stack_name)


def get_stack_outputs(cloudformation, stack_name):
    response = cloudformation.describe_stacks(StackName=stack_name)
    stack_outputs = response['Stacks'][0]['Outputs']
    return stack_outputs


def get_public_ips(stack_outputs):
    public_ip_instance_1 = next(
        (output['OutputValue'] for output in stack_outputs if output['OutputKey'] == "Instance1PublicIP"), None)

    public_ip_instance_2 = next(
        (output['OutputValue'] for output in stack_outputs if output['OutputKey'] == "Instance2PublicIP"), None)

    instances_ids = [output['OutputValue']
                     for output in stack_outputs if "InstanceID" in output['OutputKey']]

    return public_ip_instance_1, public_ip_instance_2, instances_ids


def wait_for_instances(ec2, instances_ids):
    for instance_id in instances_ids:
        waiter = ec2.get_waiter('instance_status_ok')
        waiter.wait(InstanceIds=[instance_id])


def run_flask_server(bash_script, public_ip_instance_1, public_ip_instance_2, key_name):
    os.chmod(bash_script, 0o777)

    command = ['bash', bash_script, public_ip_instance_1,
               public_ip_instance_2, f"{key_name}.pem"]

    subprocess.run(command)

    command = ['bash', bash_script, public_ip_instance_2,
               public_ip_instance_1, f"{key_name}.pem"]

    subprocess.run(command)


def main():
    random_string = create_random_string()

    region = 'us-east-1'
    stack_name = f"bar-and-niv-stack-{random_string}"
    key_name = stack_name

    print("Starting deployment")

    cloudformation, ec2 = create_clients(region)

    create_key_pair(ec2, key_name)

    template_body = read_template('managerTemplate.yaml')

    print("Creating stack request")

    response = create_stack(cloudformation, stack_name,
                            template_body, key_name)

    print(response)

    print('Waiting for stack creation to complete...')
    wait_for_stack_creation(cloudformation, stack_name)
    print('Stack creation complete.')

    stack_outputs = get_stack_outputs(cloudformation, stack_name)

    public_ip_instance_1, public_ip_instance_2, instances_ids = get_public_ips(
        stack_outputs)

    print("Waiting for instances to be running")
    wait_for_instances(ec2, instances_ids)
    print('All instances are running.')

    print("Running flask server on instances")
    run_flask_server("./set_env.sh", public_ip_instance_1,
                     public_ip_instance_2, key_name)

    print(
        f"Deployment is ready, IP1: {public_ip_instance_1}, IP2: {public_ip_instance_2}")


if __name__ == "__main__":
    main()
