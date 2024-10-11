import io
import json
import logging
from datetime import datetime, timedelta, timezone
import oci
import os

from fdk import response


REGIONS = os.environ.get("REGIONS", "ca-toronto-1,us-ashburn-1") # comma separated list of regions to export OKE cluster work requests errors
COMPARTMENTS = os.environ.get("COMPARTMENTS", "ci,crafting") # comma separated list of compartment names for which to export all OKE cluster work requests errors
POLL_INTERVAL_MINUTES = int(os.environ.get("POLL_INTERVAL_MINUTES", 30)) # this should be same as function invocation interval
TENANCY_OCID = os.environ.get("TENANCY_OCID")

DEFAULT_REGION = "us-ashburn-1"
OPERATION_FILTERS = ["NODEPOOL_UPDATE"]

logging.getLogger('oci').setLevel(logging.ERROR)

def handler(ctx, data: io.BytesIO = None):
  work_requests_errors = []
  for region in REGIONS.split(","):
    for compartment in COMPARTMENTS.split(","):
      compartment_id = get_compartment_id(compartment)
      work_requests_errors += get_work_requests_errors(
        compartment_id=compartment_id,
        operation_filters=OPERATION_FILTERS,
        region=region
      )

  for error in work_requests_errors:
    logging.error(json.dumps(error))

  return response.Response(
    ctx,
    headers={"Content-Type": "application/json"},
    response_data=json.dumps({"errors_count": len(work_requests_errors)})
  )

def get_oci_config_and_signer(region, is_local=False):
  oci_signer = None
  if is_local:
    config = oci.config.from_file()
    config["region"] = region
  else:
    config = {"region": region, "tenancy": TENANCY_OCID}
    oci_signer = oci.auth.signers.get_resource_principals_signer()

  return config, oci_signer


def get_compartment_id(compartment_name, is_local=False):
  # Get compartment id from compartment name
  config, oci_signer = get_oci_config_and_signer(DEFAULT_REGION, is_local)
  if is_local:
    identity_client = oci.identity.IdentityClient(config=config)
  else:
    identity_client = oci.identity.IdentityClient(config=config, signer=oci_signer)
  print("getting id for ", compartment_name, " in ", config["tenancy"])
  print(identity_client.list_compartments(compartment_id=config["tenancy"]).data)
  return [compartment.id for compartment in identity_client.list_compartments(compartment_id=config["tenancy"]).data if compartment.name == compartment_name][0]


def get_work_requests_errors(compartment_id, region, operation_filters, is_local=False, limit=1000):
  # Get work requests errors for the given compartment and region
  # Pagination is not implemented as the limit is set to 1000 which should be enough --
  # logging more usually don't provide much value if there were already that many errors

  config, oci_signer = get_oci_config_and_signer(region, is_local)
  if oci_signer:
    container_engine_client = oci.container_engine.ContainerEngineClient(config=config, signer=oci_signer)
  else:
    container_engine_client = oci.container_engine.ContainerEngineClient(config=config)

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
  # For testing locally
  get_work_requests_errors(
    compartment_id=get_compartment_id("ci", True),
    operation_filters=OPERATION_FILTERS,
    region="ca-toronto-1",
    is_local=True
  )
