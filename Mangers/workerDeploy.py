import boto3
import os

EC2_IP1 = os.environ.get("MY_IP")
EC2_IP2 = os.environ.get("OTHER_IP")
STACK_NAME = os.environ.get("STACK_NAME")
SECURITY_GROUP = os.environ.get("SECURITY_GROUP_ID")

try:
    region = 'us-east-1'
    ec2 = boto3.client('ec2', region_name="us-east-1")
    print(
        f"EC2_IP1: {EC2_IP1}, EC2_IP2:{EC2_IP2} , SECURITY_GROUP:{SECURITY_GROUP} ")

    response = ec2.run_instances(
        ImageId="ami-042e8287309f5df03",
        InstanceType="t2.micro",
        SecurityGroups=[SECURITY_GROUP],
        MinCount=1,
        MaxCount=1,
        UserData=f'''#!/bin/bash
      sudo apt update -y
      sudo apt install -y python3
      sudo apt install -y python3-pip
      sudo apt install -y git
      echo "export EC2IP1={EC2_IP1}" | sudo tee -a /etc/environment
      echo "export EC2IP2={EC2_IP2}" | sudo tee -a /etc/environment
      source /etc/environment
      git clone https://github.com/bar-nir/cloud-computing-ex2.git
      cd cloud-computing-ex2/Worker
      sudo chmod 777 app.py
      sudo pip3 install -r requirements.txt
      sudo python3 app.py
    ''',
    )
    print("EC2 created:", response)
except Exception as e:
    print(f"Error: {e}")
