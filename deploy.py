import random
import os
import boto3
import paramiko


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


def run_flask_server(public_ip_instance_1, public_ip_instance_2, key_name):
    key = paramiko.RSAKey(filename=f"{key_name}.pem")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    bash_commands = '''
        sudo apt install -y python3
        sudo apt install -y python3-pip
        sudo apt install -y git &
        echo "export OTHER_IP={other_ip}" | sudo tee -a /etc/environment
        echo "export MY_IP={instance_ip}" | sudo tee -a /etc/environment
        source /etc/environment
        git clone https://github.com/bar-nir/cloud-computing-ex2.git
        cd cloud-computing-ex2/Mangers
        sudo chmod 777 app.py
        sudo pip3 install -r requirements.txt
        sudo nohup python3 app.py > flask.log 2>&1 &
    '''

    print(f"Starting ssh to IP: {public_ip_instance_1}")
    ssh.connect(public_ip_instance_1, username='ubuntu', pkey=key)
    stdin, stdout, stderr = ssh.exec_command(bash_commands.format(
        other_ip=public_ip_instance_2, instance_ip=public_ip_instance_1))

    output = stdout.read().decode()
    print(output)
    ssh.close()

    print(f"Server with IP: {public_ip_instance_1} is ready to use")

    print(f"Starting ssh to IP: {public_ip_instance_2}")
    ssh.connect(public_ip_instance_2, username='ubuntu', pkey=key)
    stdin, stdout, stderr = ssh.exec_command(bash_commands.format(
        other_ip=public_ip_instance_1, instance_ip=public_ip_instance_2))
    output = stdout.read().decode()
    print(output)
    ssh.close()

    print(f"Server with IP: {public_ip_instance_2} is ready to use")

    print("SSH Finished")


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
    run_flask_server(public_ip_instance_1,
                     public_ip_instance_2, key_name)

    print(
        f"Deployment is ready, IP1: {public_ip_instance_1}, IP2: {public_ip_instance_2}")


if __name__ == "__main__":
    main()
