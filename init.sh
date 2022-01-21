#!/bin/bash

# Init a Virtual Env
echo "Create Virtual Environment..."
python3 -m venv venv

echo "Enabling Virtual Environment..."
source ./venv/bin/activate

pip install -r requirements.txt
