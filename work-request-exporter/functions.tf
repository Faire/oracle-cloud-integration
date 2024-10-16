resource "oci_functions_application" "work_request_exporter_function_app" {
  depends_on     = [data.oci_core_subnet.input_subnet]
  compartment_id = var.compartment_ocid
  config = {
    "REGIONS" = var.regions
    "COMPARTMENTS" = var.compartments
    "POLL_INTERVAL_MINUTES" = var.poll_interval_minutes
    "TENANCY_OCID" = var.tenancy_ocid
  }
  defined_tags  = {}
  display_name  = "${var.resource_name_prefix}-function-app"
  freeform_tags = local.freeform_tags
  network_security_group_ids = [
  ]
  shape = var.function_app_shape
  subnet_ids = [
    data.oci_core_subnet.input_subnet.id,
  ]

  lifecycle {
    ignore_changes = [
      defined_tags["Oracle-Tags.CreatedBy"],
      defined_tags["Oracle-Tags.CreatedOn"],
    ]
  }
}

resource "oci_functions_function" "work_request_exporter_function" {
  depends_on = [null_resource.FnImagePushToOCIR, oci_functions_application.work_request_exporter_function_app]
  #Required
  application_id = oci_functions_application.work_request_exporter_function_app.id
  display_name   = "work-request-exporter"
  memory_in_mbs  = "256"

  #Optional
  defined_tags  = {}
  freeform_tags = local.freeform_tags
  image         = local.user_image_provided ? local.custom_image_path : local.docker_image_path

  timeout_in_seconds = var.function_timeout_secs

  lifecycle {
    ignore_changes = [
      defined_tags["Oracle-Tags.CreatedBy"],
      defined_tags["Oracle-Tags.CreatedOn"]
    ]
  }
}
