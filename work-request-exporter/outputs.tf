output "function_id" {
  value = oci_functions_function.work_request_exporter_function.id
}

output "function_app_name" {
  value = oci_functions_application.work_request_exporter_function_app.display_name
}