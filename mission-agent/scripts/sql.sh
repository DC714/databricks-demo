#!/bin/bash
# Usage: mission-agent/scripts/sql.sh "<SQL>" <warehouse_id>   (prints rows as tab-separated text)
D=${DATABRICKS_BIN:-databricks}
$D api post /api/2.0/sql/statements --json "{\"warehouse_id\":\"$2\",\"statement\":$(python3 -c "import json,sys;print(json.dumps(sys.argv[1]))" "$1"),\"wait_timeout\":\"50s\"}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if d['status']['state']!='SUCCEEDED': print(d['status'])
else:
    for r in d.get('result',{}).get('data_array',[]): print('\t'.join('' if x is None else str(x) for x in r))"
