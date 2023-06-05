import time
import hashlib
import requests


def work(data, iterations):
    output = hashlib.sha512(data).digest()
    for i in range(iterations - 1):
        output = hashlib.sha512(output).digest()
    return output


def process_job():
    request_jobs_attempts = 0
    while True:
        if request_jobs_attempts > 10:
            "TERMINATE WORKER"
        time.sleep(1)
        request_jobs_attempts += 1
        try:
            manger1_queue_length = requests.get("MANGER_IP1/length").json()
        except:
            manger1_queue_length = 0
        try:
            manger2_queue_length = requests.get("MANGER_IP2/length").json()
        except:
            manger2_queue_length = 0
        manger_IP = "MANGER_IP1" if manger1_queue_length > manger2_queue_length else "MANGER_IP2"
        other_manger_IP = "MANGER_IP2" if manger1_queue_length > manger2_queue_length else "MANGER_IP1"
        if manger1_queue_length == 0 and manger2_queue_length == 0:
            continue
        try:
            job = requests.get(f'{manger_IP}/worker/job').json()
        except:
            continue
        if job is not None:
            result = work(job.data, job.iterations)
            job["data"] = result
            try:
                requests.post(f'{manger_IP}/worker/completed', data=job).json()
            except:
                try:
                    requests.post(f'{other_manger_IP}/worker/completed',
                                  data=job).json()
                except:
                    continue
            request_jobs_attempts = 0


if __name__ == '__main__':
    process_job()
