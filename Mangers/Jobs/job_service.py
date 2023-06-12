import json
import threading
import time
import uuid
import requests
from datetime import datetime, timedelta
import queue
import os
import boto3


class JobService():

    def __init__(self):
        self.incompleted_jobs = queue.Queue()
        self.worksers = 0
        self.max_workers = 3
        self.MY_IP = os.environ.get('MY_IP')
        self.other_manager_ip = os.environ.get('OTHER_IP')
        self.is_deploy_in_progress = False
        self.completed_jobs = queue.Queue()
        self.treshhold_to_pass_message = 3
        self.sleep_time = 10
        threading.Thread(target=self.scale_workers).start()

    def add_job(self, iterations: int, data: str) -> str:
        print(data, iterations)
        id = str(uuid.uuid4())
        current_job = ({"id": id, "iterations": iterations,
                       'date': datetime.now().isoformat(), "data": data})
        other_manager_queue_length = requests.get(
            f'http://{self.other_manager_ip}:5000/length', timeout=5).json()

        if (self.incompleted_jobs.qsize() - self.treshhold_to_pass_message > other_manager_queue_length):

            self.incompleted_jobs.put(current_job)
            json_data = json.dumps(current_job)
            requests.put(f'http://{self.other_manager_ip}:5000/manager/add',
                         json=json_data, timeout=5)
        else:
            self.incompleted_jobs.put(current_job)

        return id

    def scale_workers(self):
        while True:
            time.sleep(self.sleep_time)
            if self.is_deploy_in_progress == False and not self.incompleted_jobs.empty():
                current_job = self.incompleted_jobs.queue[0]
                if self.max_workers > self.worksers \
                        and datetime.now() - datetime.fromisoformat(current_job["date"]) > timedelta(seconds=10):
                    try:
                        self.is_deploy_in_progress = True
                        self.deploy_new_worker()
                    except Exception as e:
                        print(f"error in deploying new worker {e}")

    def get_next_job(self):
        if not self.incompleted_jobs.empty():
            return self.incompleted_jobs.get()
        else:
            return None

    def delete_worker(self):
        self.worksers -= 1
        print(f"deleted worker current workers:{self.worksers}")
        return True

    def get_n_last_completed_jobs(self, from_request: str, top: int):
        jobs = []
        while (self.completed_jobs.qsize() and top):
            current_job = self.completed_jobs.get()["id"]
            jobs.append(current_job)
            top = top - 1
        print(f"finished getting localy jobs: {jobs} ")
        print(from_request, top)
        if top and from_request != 'manager':
            print(f"getting jobs from other manager")
            other_mangaer_jobs = requests.post(
                f'http://{self.other_manager_ip}:5000/pullCompleted?top={top}&from=manager', timeout=5).json()
            jobs += other_mangaer_jobs

        print(f"total jobs {jobs} ")
        return jobs

    def add_completed_job(self, data: object):
        print(f"completed job {data}")
        self.completed_jobs.put(data)
        return True

    def deploy_new_worker(self):
        EC2_IP1 = os.environ.get("MY_IP")
        EC2_IP2 = os.environ.get("OTHER_IP")
        SECURITY_GROUP = os.environ.get("SECURITY_GROUP_ID")
        try:
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
            instance_id = response['Instances'][0]['InstanceId']
            print(f'Launching instance {instance_id}...')
            waiter = ec2.get_waiter('instance_status_ok')
            waiter.wait(InstanceIds=[instance_id])
            print(f'Instance {instance_id} is running.')
            self.is_deploy_in_progress = False
            self.worksers += 1
        except Exception as e:
            self.is_deploy_in_progress = False
            print(f"Error: {e}")
