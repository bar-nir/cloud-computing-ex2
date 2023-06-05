import json
import uuid
import requests
from datetime import datetime, timedelta
import queue
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import os
import logging


class JobService():

    def __init__(self):
        self.incompleted_jobs = queue.Queue()
        self.worksers = 0
        self.max_workers = 3
        self.MY_IP = os.environ.get('MY_IP')
        self.other_manager_ip = os.environ.get('OTHER_IP')
        self.completed_jobs = queue.Queue()
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(self.scale_workers, 'interval', seconds=30)
        self.treshhold_to_pass_message = 3
        scheduler.start()

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
        if not self.incompleted_jobs.empty():
            current_job = self.incompleted_jobs.queue[0]
            if self.max_workers > self.worksers \
                    and datetime.now() - datetime.fromisoformat(current_job["date"]) > timedelta(seconds=10):
                try:

                    subprocess.Popen(['python3', "./workerDeploy.py"])
                    self.worksers += 1
                except Exception as e:
                    logging.error(e)

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
