This guide will help you set up the project and deploy it to AWS

1. clone the project and install requirements

```bash
git clone git@github.com:bar-nir/cloud-computing-ex2.git
```

```bash
cd cloud-computing-ex2
```

```bash
pip3 install -r requirements.txt
```

2. Deploy

```bash
python3 deploy.py
```

## document detailing failure modes and how to deal with them if this was a real-world project.

Can be found under the main repo with file name `failure modes.pdf`

# Job Management API

This API provides an interface for managing jobs and workers in a system.

## Enqueue Job

- **URL:** `EC2_IP:5000/enqueue?iterations=10`
- **Method:** `PUT`

* example:

```
curl --location --request PUT '3.235.135.117:5000/enqueue?iterations=10' \
--header 'Content-Type: application/json' \
--data-raw '"asdasdasdasdasdasdasdakljfaljfadjfdahjfadhjk"'
```

## Get completed jobs

- **URL:** `EC2_IP:5000/pullCompleted?top=5`
- **Method:** `POST`
- **example**:

```
curl --location --request POST '3.235.135.117:5000/pullCompleted?top=10'
```

# Set Scale Worker Time Delta

- **URL:** `http://EC2_IP:5000/scale-worker-time-delta`
- **Method:** `POST`

- **Description:**
  This route can be used to change how the auto-scaling mechanism works.

- **Parameters:**

  - `scale_delta`: Time in seconds between checking if another EC2 instance needs to be scaled up. It only checks when there is no other EC2 from the same manager in the deployment process.
  - `worker_delta`: Time between each call for a worker to ask for work from an EC2 manager.
  - defaults set to `worker_delta = 5`, `scale_delta = 3`
  - ### `To see different scaling results, please play with these variables.`

- **example**:

```
curl --location --request POST '3.235.135.117:5000/scale-worker-time-delta' \
--header 'Content-Type: application/json' \
--data-raw '{
    "scale_delta": 1,
    "worker_delta": 5
}'
```

## Get Incomplete Jobs Length

- **URL:** `EC2_IP:5000/length`
- **Method:** `GET`
- **example**:

```
curl --location --request GET '3.235.135.117:5000/length'
```

# Routes that the system uses.

- In the future this routes should only be expose to the system and not the users.

## Get Incomplete Jobs Length

- **URL:** `EC2_IP:5000/length`
- **Method:** `GET`
- **example**:

```
curl --location --request GET '3.235.135.117:5000/length'
```

## Delete Worker (remove current number of workers)

- **URL:** `EC2_IP:5000/worker`
- **Method:** `DELETE`
- **Description:**
  The worker uses it before terminating itself to inform the manager that it is scaling down.
- **example**:

```
curl -X DELETE 3.235.135.117:5000/worker
```

## Add completed job to manager

- **URL:** `EC2_IP:5000/worker/completed`
- **Method:** `POST`
- **Description:**
  The worker uses it to inform the manager about the completed job.
- **example**:

```
curl -X POST -H "Content-Type: application/json" -d '{"id": "60", "date": "10","iterations": "10","data": "hashed string"}' "3.235.135.117:5000/worker/completed"
```

## Get job from manager to worker

- **URL:** `EC2_IP:5000/worker/job`
- **Method:** `GET`
- **Description:**
  The worker uses it to retrieve incomplete jobs from a manager.
- **example**:

```
curl 3.235.135.117:5000/worker/job
```

## Add incompleted job to manager by other manager

- **URL:** `EC2_IP:5000/manager/add`
- **Method:** `PUT`
- **Description:**
  The managers use this route to load balance the jobs among themselves.
- **example**:

```
curl --location --request PUT '3.235.135.117:5000/manager/add' \
--header 'Content-Type: application/json' \
--data-raw '{"id": "60", "date": "10","iterations": "10","data": "string to hash"}'
```

## Get completed jobs

- **URL:** `EC2_IP:5000/pullCompleted?top=5&from=manager`
- **Method:** `POST`
- **Description:**
  With the query parameter `from=manager`, managers can identify that the request is sent by another manager. They then supply the last 'n' completed jobs to be retrieved by the user. These managers merge their local jobs with the jobs fetched from the other manager.
- **example**:

```
curl --location --request POST '3.235.135.117:5000/pullCompleted?top=10&from=manager'
```
