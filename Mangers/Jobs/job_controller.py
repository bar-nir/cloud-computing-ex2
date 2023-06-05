from flask import Blueprint, request, jsonify
from Jobs.job_service import JobService


job_controller = Blueprint('job_controller', __name__)
job_service = JobService()


@job_controller.route('/enqueue', methods=['PUT'])
def enqueue_job():
    iterations = int(request.args.get('iterations'))
    body = request.get_json()
    job_service.add_job(iterations, body)


@job_controller.route('/manager/add', methods=['PUT'])
def add_job():
    job = request.get_json()
    job_service.incompleted_jobs.put(job)
    return jsonify({'message': 'Job added'}), 200


@job_controller.route('/length', methods=['GET'])
def get_incompleted_jobs_length():
    return jsonify(job_service.incompleted_jobs.qsize()), 200


@job_controller.route('/worker/job', methods=['GET'])
def get_next_job_for_worker():
    return jsonify(job_service.get_next_job()), 200


@job_controller.route('/worker', methods=['DELETE'])
def get_next_job_for_worker():
    job_service.delete_worker()
    return jsonify("DELETED"), 200


@job_controller.route('/pullCompleted', methods=['POST'])
def get_completed_jobs():
    from_reqeuest = request.args.get('from')
    top = int(request.args.get('top'))
    last_top_jobs = job_service.get_n_last_completed_jobs(from_reqeuest, top)
    return jsonify(last_top_jobs), 200


@job_controller.route('/worker/completed', methods=['POST'])
def add_completed_job():
    job = request.get_json()
    job_service.add_completed_job(job)
    return jsonify("ADDED"), 200
