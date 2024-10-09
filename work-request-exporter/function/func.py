import io
import json
import logging
from datetime import datetime, timedelta, timezone
import oci
import os

from fdk import response


regions = os.environ.get("REGIONS", "ca-toronto-1,us-ashburn-1")
compartment_ids = os.environ.get("COMPARTMENT_IDS", "ocid1.compartment.oc1..aaaaaaaanydaqleheyo7hepeg6lsvplv7igvfarnomdigsk253h3mxkxjocq,ocid1.compartment.oc1..aaaaaaaaqzxstunqgzwnvfyrg5xoj4glcqqkygszmlljx4ke4epqiynce2pq")
POLL_INTERVAL_MINUTES = os.environ.get("POLL_INTERVAL_MINUTES", 30) # this should be same as function invocation interval
operation_filters = ["NODEPOOL_UPDATE"]

logging.getLogger('oci').setLevel(logging.ERROR)

def handler(ctx, data: io.BytesIO = None):
  work_requests_errors = []
  for region in regions.split(","):
    for compartment_id in compartment_ids.split(","):
      work_requests_errors += get_work_requests_errors(
        compartment_id=compartment_id,
        operation_filters=operation_filters,
        region=region
      )

  for error in work_requests_errors:
    logging.error(json.dumps(error))

  return response.Response(
    ctx,
    headers={"Content-Type": "application/json"},
    response_data=json.dumps({"errors_count": len(work_requests_errors)})
  )


def get_work_requests_errors(compartment_id, region, operation_filters = ["NODEPOOL_UPDATE"], is_local=False, limit=1000):
  if is_local:
    config = oci.config.from_file()
    config["region"] = region
    container_engine_client = oci.container_engine.ContainerEngineClient(config=config)
  else:
    oci_signer = oci.auth.signers.get_resource_principals_signer()
    container_engine_client = oci.container_engine.ContainerEngineClient(config={region: region}, signer=oci_signer)

  cluster_name_map = {cluster.id: cluster.name for cluster in container_engine_client.list_clusters(compartment_id=compartment_id).data}
  nodepool_name_map = {cluster.id: cluster.name for cluster in container_engine_client.list_node_pools(compartment_id=compartment_id).data}

  list_work_requests_response = container_engine_client.list_work_requests(
    compartment_id=compartment_id,
    resource_type="CLUSTER",
    status=["FAILED"],
    sort_by="TIME_STARTED",
    sort_order="DESC",
    limit=limit,
  )

  work_requests_errors = []
  now = datetime.now(tz=timezone.utc)
  for work_request_summary in list_work_requests_response.data:
    if work_request_summary.operation_type in operation_filters and work_request_summary.time_started > (now - timedelta(minutes=POLL_INTERVAL_MINUTES)):
      errors = container_engine_client.list_work_request_errors(
        compartment_id=compartment_id,
        work_request_id=work_request_summary.id
      ).data
      cluster_id = [resource for resource in work_request_summary.resources if resource.entity_type == 'cluster'][0].identifier
      nodepool_id = [resource for resource in work_request_summary.resources if resource.entity_type == 'nodepool'][0].identifier
      work_requests_errors += [{
        "region": region,
        "compartment_id": compartment_id,
        "cluster": cluster_name_map[cluster_id],
        "node_pool": nodepool_name_map[nodepool_id],
        "work_request_id": work_request_summary.id,
        "error": error.message,
        "time": work_request_summary.time_started.isoformat(),
      } for error in errors]

  return work_requests_errors

if __name__ == "__main__":
  get_work_requests_errors(
    compartment_id="ocid1.compartment.oc1..aaaaaaaanydaqleheyo7hepeg6lsvplv7igvfarnomdigsk253h3mxkxjocq",
    region="ca-toronto-1",
    is_local=True
  )
