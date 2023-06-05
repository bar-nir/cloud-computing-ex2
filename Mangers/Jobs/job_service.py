import uuid
import requests
from datetime import datetime, timedelta
import queue
from apscheduler.schedulers.background import BackgroundScheduler


class JobService():

    def __init__(self):
        self.incompleted_jobs = queue.Queue()
        self.worksers = 0
        self.max_workers = 3
        self.completed_jobs = queue.Queue()
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(self.scale_workers, 'interval', seconds=10)
        scheduler.start()

    def add_job(self, iterations: int, data: str) -> str:
        id = str(uuid.uuid4())
        current_job = ({"id": id, "itteration": iterations,
                       'date': datetime.now(), "data": data})
        other_manager_queue_length = requests.get(
            "ORHTER_MANAGER_IP/length").json()
        if (other_manager_queue_length > self.incompleted_jobs.qsize()):
            self.incompleted_jobs.put(current_job)
        else:
            requests.put("ORHTER_MANAGER_IP/manager/add",
                         json=current_job)
        return id

    def scale_workers(self):
        if not self.incompleted_jobs.empty():
            current_job = self.incompleted_jobs[0]
            if self.max_workers < len(self.worksers) \
                    and current_job["date"] - datetime.now() > timedelta(seconds=10):
                "SCALE WORKERS"

    def get_next_job(self):
        if not self.incompleted_jobs.empty():
            return self.incompleted_jobs.get()
        else:
            return None

    def delete_worker(self):
        self.worksers -= 1
        return True

    def get_n_last_completed_jobs(self, from_request: str, top: int):
        jobs = []
        while (self.completed_jobs.qsize() and top):
            current_job = self.completed_jobs.get()["id"]
            jobs.append(current_job)
            top -= -1
        if top and from_request != 'manager':
            other_mangaer_jobs = requests.post(
                f'ORHTER_MANAGER_IP/pullCompleted?top={top}&from=manager').json()
            jobs += other_mangaer_jobs
        return jobs

    def add_completed_job(self, data: object):
        self.completed_jobs.put(data)
        return True
