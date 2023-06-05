#!/bin/bash
INSTANCE_IP="$1"
OTHER_IP="$2"
KEY_PATH="$3"
INSTANCE_USER="ubuntu"

ssh -o IdentitiesOnly=yes -o StrictHostKeyChecking=no -i "$KEY_PATH" "$INSTANCE_USER"@"$INSTANCE_IP" << EOF
  echo "export OTHER_IP=$OTHER_IP" | sudo tee -a /etc/environment
  echo "export MY_IP=${INSTANCE_IP}" | sudo tee -a /etc/environment
  source /etc/environment
  git clone https://github.com/bar-nir/cloud-computing-ex2.git
  cd cloud-computing-ex2/Mangers
  sudo chmod 777 app.py
  sudo pip3 install -r requirements.txt
  sudo nohup python3 app.py > flask.log 2>&1 &
EOF