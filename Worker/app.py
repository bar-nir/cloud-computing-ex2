import time
import hashlib
import requests
import os
import subprocess


def work(data, iterations):
    output = hashlib.sha512(data.encode()).digest()
    for i in range(iterations - 1):
        output = hashlib.sha512(output).digest()
    return output


def notify_manager_worker_is_alive(ip, retries=4, delay=2):
    for i in range(retries):
        try:
            print("notifying manager worker is alive")
            requests.post(f"http://{ip}:5000/worker-has-started", timeout=3)
            return
        except Exception as e:
            print(f"Error: {e}")
            if i < retries - 1:
                time.sleep(delay)


def process_job():
    EC2_IP1 = os.environ.get("EC2IP1")
    SLEEP_TIME = int(os.environ.get("WORKER_DELTA", "6"))
    EC2_IP2 = os.environ.get("EC2IP2")
    request_jobs_attempts = 0
    MAX_RETRY = 4
    notify_manager_worker_is_alive(EC2_IP1)
    print(f"EC2_IP1: {EC2_IP1}, EC2_IP2:{EC2_IP2}")
    while True:
        print(f"in attempt: {request_jobs_attempts}")
        if request_jobs_attempts > MAX_RETRY:
            print(f"shutting down server")
            subprocess.run(['bash', './terminate_ec2.sh'])
        time.sleep(SLEEP_TIME)
        request_jobs_attempts += 1
        try:
            manger1_queue_length = requests.get(
                f"http://{EC2_IP1}:5000/length", timeout=3).json()
        except Exception as e:
            print(f"Error: {e}")
            manger1_queue_length = 0
        try:

            manger2_queue_length = requests.get(
                f"http://{EC2_IP2}:5000/length", timeout=3).json()
        except Exception as e:
            print(f"Error: {e}")
            manger2_queue_length = 0
        manger_IP = EC2_IP1 if manger1_queue_length > manger2_queue_length else EC2_IP2
        other_manger_IP = EC2_IP2 if manger1_queue_length > manger2_queue_length else EC2_IP1
        if manger1_queue_length == 0 and manger2_queue_length == 0:
            continue
        try:
            job = requests.get(
                f'http://{manger_IP}:5000/worker/job', timeout=3).json()
        except Exception as e:
            print(f"Error: {e}")
            continue
        print(f"job affter fetching: {job}")
        if job is not None:
            result = work(job["data"], job["iterations"])
            job["data"] = str(result)

            try:
                json_data = job
                print(f"sending finish")
                requests.post(f'http://{manger_IP}:5000/worker/completed',
                              json=json_data, timeout=3)
            except Exception as e:
                print(f"Error: {e}")
                try:
                    print(f"sending finish")
                    requests.post(f'http://{other_manger_IP}:5000/worker/completed',
                                  json=json_data, timeout=3)
                except Exception as e:
                    print(f"Error: {e}")
                    continue
            request_jobs_attempts = 0


if __name__ == '__main__':
    process_job()
