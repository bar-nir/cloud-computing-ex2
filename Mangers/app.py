#!flask/bin/python
from flask import Flask
from Jobs.job_controller import job_controller


app = Flask(__name__)
app.register_blueprint(job_controller)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
