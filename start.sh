#!/bin/bash

echo 'Starting Evaluation Neo4J Application...'

source venv/bin/activate
pip install -r requirements.txt
host='localhost'
port=8000
app_name="app"
if [[ $# -eq 3 ]]; then
  echo "Use script parameters..."
  host="$1"
  port="$2"
  app_name="$3"
fi
uvicorn main:"${app_name}" --reload --port "$port" --host "${host}"