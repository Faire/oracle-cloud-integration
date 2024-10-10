resource "oci_resource_scheduler_schedule" "work_request_exporter_scheduler" {
  action = "START_RESOURCE"
  compartment_id = var.tenancy_ocid
  recurrence_details = "* */1 * * *"
  recurrence_type = "CRON"

  resources {
    id = oci_functions_function.work_request_exporter_function.id
  }
}