#!/bin/bash
# Usage: mission-agent/scripts/create_vector_index.sh <catalog> <warehouse_id>
# Creates a Vector Search endpoint and a Delta Sync index over self-managed 384-dimension embeddings.
# Needs notebook 01 to have run (tables ma.chunks and ma.chunk_embeddings). Free Edition allows one endpoint.
set -e
D=${DATABRICKS_BIN:-databricks}
C=$1
$D vector-search-endpoints create-endpoint mission-agent-vs STANDARD --no-wait
$D api post /api/2.0/sql/statements --json "{\"warehouse_id\":\"$2\",\"wait_timeout\":\"50s\",\"statement\":\"CREATE OR REPLACE TABLE $C.ma.chunk_vectors TBLPROPERTIES (delta.enableChangeDataFeed = true) AS SELECT c.chunk_id, c.doc_id, c.page, c.text, e.embedding FROM $C.ma.chunks c JOIN $C.ma.chunk_embeddings e USING (chunk_id)\"}" >/dev/null
$D vector-search-indexes create-index --json "{\"name\":\"$C.ma.chunk_index\",\"endpoint_name\":\"mission-agent-vs\",\"primary_key\":\"chunk_id\",\"index_type\":\"DELTA_SYNC\",\"delta_sync_index_spec\":{\"source_table\":\"$C.ma.chunk_vectors\",\"pipeline_type\":\"TRIGGERED\",\"embedding_vector_columns\":[{\"name\":\"embedding\",\"embedding_dimension\":384}],\"columns_to_sync\":[\"doc_id\",\"page\",\"text\"]}}" >/dev/null
echo "Index requested. It can take 15 to 20 minutes to come online: databricks vector-search-indexes get-index $C.ma.chunk_index"
