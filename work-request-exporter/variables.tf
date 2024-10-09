variable "resource_name_prefix" {
  type        = string
  description = "The prefix for the name of all of the resources"
  default     = "datadog-logs"
}

variable "create_vcn" {
  type        = bool
  default     = true
  description = "Optional variable to create virtual network for the setup. True by default"
}

variable "function_subnet_id" {
  type        = string
  default     = ""
  description = "The OCID of the subnet to be used for the function app. Required if not creating the VCN"
}

variable "function_image_path" {
  type        = string
  default     = ""
  description = "The full path of the function image. The image should be present in the container registry for the region"
}

variable "function_app_shape" {
  type        = string
  default     = "GENERIC_ARM"
  description = "The shape of the function application. The docker image should be built accordingly. Use ARM if using Oracle Resource managaer stack"
  validation {
    condition     = contains(["GENERIC_ARM", "GENERIC_X86", "GENERIC_X86_ARM"], var.function_app_shape)
    error_message = "Valid values are: GENERIC_ARM, GENERIC_X86, GENERIC_X86_ARM."
  }
}

variable "oci_docker_username" {
  type        = string
  default     = ""
  sensitive   = true
  description = "The docker login username for the OCI container registry. Used in creating function image. Not required if the image is already exists."
}

variable "oci_docker_password" {
  type        = string
  default     = ""
  sensitive   = true
  description = "The auth password for docker login to OCI container registry. Used in creating function image. Not required if the image already exists."
}

variable "function_timeout_secs" {
  type        = number
  description = "The timeout in seconds for the function"
  default     = 60
}

variable "regions" {
  type        = string
  description = "The regions to monitor for work requests. Comma separated list of regions"
}

variable "compartment_ids" {
  type        = string
  description = "The compartment OCIDs to monitor for work requests. Comma separated list of compartment OCIDs"
}

variable "poll_interval_minutes" {
  type        = number
  description = "The interval in minutes to poll for work requests. Should be same as function invocation interval"
}

#*************************************
#         TF auth Requirements
#*************************************
variable "tenancy_ocid" {
  type        = string
  description = "OCI tenant OCID, more details can be found at https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm#five"
}
variable "region" {
  type        = string
  description = "OCI Region as documented at https://docs.cloud.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm"
}
variable "compartment_ocid" {
  type        = string
  description = "The compartment OCID to deploy resources to"
}
