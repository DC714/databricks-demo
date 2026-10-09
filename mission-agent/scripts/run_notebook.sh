#!/bin/bash
# Usage: scripts/run_notebook.sh 01_ingest_bronze
# Imports notebooks/<name>.py into your workspace and runs it as a one-time serverless job.
# Prints only the notebook's exit value. Requires a signed-in Databricks CLI.
set -e
D=${DATABRICKS_BIN:-databricks}
N=$1
ME=$($D current-user me | python3 -c "import sys,json;print(json.load(sys.stdin)['userName'])")
P=/Users/$ME/databricks-demo-agent/$N
$D workspace import "$P" --file "mission-agent/notebooks/$N.py" --format SOURCE --language PYTHON --overwrite
RUN=$($D jobs submit --no-wait --json "{\"run_name\":\"$N\",\"tasks\":[{\"task_key\":\"t\",\"notebook_task\":{\"notebook_path\":\"$P\"}}]}" | python3 -c "import sys,json;print(json.load(sys.stdin)['run_id'])")
until [ "$($D jobs get-run $RUN | python3 -c "import sys,json;print(json.load(sys.stdin)['state']['life_cycle_state'])")" = "TERMINATED" ] || [ "$($D jobs get-run $RUN | python3 -c "import sys,json;print(json.load(sys.stdin)['state']['life_cycle_state'])")" = "INTERNAL_ERROR" ]; do sleep 10; done
TASK=$($D jobs get-run $RUN | python3 -c "import sys,json;print(json.load(sys.stdin)['tasks'][0]['run_id'])")
$D jobs get-run-output $TASK | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('notebook_output',{}).get('result') or str(d.get('error'))[:600]);print((d.get('error_trace') or '')[-700:])"
