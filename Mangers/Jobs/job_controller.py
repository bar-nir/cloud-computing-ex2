from flask import Blueprint, request, jsonify
from Jobs.job_service import JobService
import os
import logging

job_controller = Blueprint('job_controller', __name__)
job_service = JobService()


@job_controller.route('/enqueue', methods=['PUT'])
def enqueue_job():
    try:
        logging.info("In equeue")
        iterations = int(request.args.get('iterations'))
        body = request.get_json()
        print(body)
        id = job_service.add_job(iterations, body)
        return jsonify({'message': f'Job added with id:{id}'}), 200
    except Exception as e:

        return jsonify({'message': 'Error'}), 500


@job_controller.route('/manager/add', methods=['PUT'])
def add_job():
    try:
        job = request.get_json()
        job_service.incompleted_jobs.put(job)
        return jsonify({'message': 'Job added'}), 200
    except Exception as e:
        return jsonify({'message': f'Error: {e}'}), 500


@job_controller.route('/length', methods=['GET'])
def get_incompleted_jobs_length():
    try:
        return jsonify(job_service.incompleted_jobs.qsize()), 200
    except Exception as e:
        return jsonify({'message': f'Error: {e}'}), 500


@job_controller.route('/worker/job', methods=['GET'])
def get_next_job_for_worker():
    try:
        return jsonify(job_service.get_next_job()), 200
    except Exception as e:
        return jsonify({'message': f'Error: {e}'}), 500


@job_controller.route('/worker', methods=['DELETE'])
def delete_worker():
    try:
        job_service.delete_worker()
        return jsonify("DELETED"), 200
    except Exception as e:
        return jsonify({'message': f'Error: {e}'}), 500


@job_controller.route('/pullCompleted', methods=['POST'])
def get_completed_jobs():
    try:
        print(request.args)
        from_reqeuest = request.args.get('from')
        top = int(request.args.get('top'))
        print(from_reqeuest, top)
        last_top_jobs = job_service.get_n_last_completed_jobs(
            from_reqeuest, top)
        return jsonify(last_top_jobs), 200
    except Exception as e:
        return jsonify({'message': f'Error: {e}'}), 500


@job_controller.route('/worker/completed', methods=['POST'])
def add_completed_job():
    try:
        print("in completed jobx")
        job = request.get_json()
        job_service.add_completed_job(job)
        return jsonify("ADDED"), 200
    except Exception as e:
        return jsonify({'message': f'Error: {e}'}), 500

@job_controller.route('/scale-worker-time-delta', methods=['POST'])
def set_scale_worker_time_delta():
    try:
        time_delta = request.get_json()
        job_service.set_time_deltas(time_delta)
        return jsonify("Seted"), 200
    except Exception as e:
        return jsonify({'message': f'Error: {e}'}), 500
