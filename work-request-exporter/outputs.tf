output "function_id" {
  value = oci_functions_function.work_request_exporter_function.id
}

output "function_log_group_id" {
  value = module.work_request_exporter_logging.func_loggroupid
}

output "function_log_id" {
  value = module.work_request_exporter_logging.func_logid
}