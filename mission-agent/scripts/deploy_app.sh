#!/bin/bash
# Usage: mission-agent/scripts/deploy_app.sh <catalog> <warehouse_id>
# Creates and deploys the Streamlit front end as a Databricks App. Free Edition allows one app.
# Needs the Vector Search index from create_vector_index.sh. Sign in to the workspace to open the app URL.
set -e
D=${DATABRICKS_BIN:-databricks}
C=${1:-workspace}
ME=$($D current-user me | python3 -c "import sys,json;print(json.load(sys.stdin)['userName'])")
$D apps create mission-agent-app --description "Learning project: cited question answering over public NIST documents" --no-wait >/dev/null
$D workspace import-dir mission-agent/app /Users/$ME/mission-agent-app --overwrite >/dev/null
echo "Wait until the app compute is ACTIVE (databricks apps get mission-agent-app), then:"
echo "1. Grant its service principal (service_principal_client_id from 'apps get'):"
echo "   GRANT USE CATALOG ON CATALOG $C TO \`<client_id>\`; GRANT USE SCHEMA ON SCHEMA $C.ma TO \`<client_id>\`;"
echo "   GRANT SELECT ON TABLE $C.ma.chunk_index TO \`<client_id>\`;"
echo "2. databricks apps update mission-agent-app --json '{\"resources\":[{\"name\":\"gemma\",\"serving_endpoint\":{\"name\":\"databricks-gemma-3-12b\",\"permission\":\"CAN_QUERY\"}},{\"name\":\"llama\",\"serving_endpoint\":{\"name\":\"databricks-meta-llama-3-1-8b-instruct\",\"permission\":\"CAN_QUERY\"}}]}'"
echo "3. databricks apps deploy mission-agent-app --source-code-path /Workspace/Users/$ME/mission-agent-app"
