variable "tenancy_ocid" {
  type = string
}

variable "user_ocid" {
  type = string
}

variable "fingerprint" {
  type = string
}

variable "private_key_path" {
  type = string
}

variable "region" {
  type    = string
  default = "eu-frankfurt-1"
}

variable "compartment_ocid" {
  type = string
}

variable "amd_count" {
  type    = number
  default = 2
}

variable "arm_count" {
  type    = number
  default = 0
}

variable "ad_index" {
  type    = number
  default = 0
}

variable "proxy_port" {
  type    = number
  default = 8888
}

variable "proxy_user" {
  type    = string
  default = "tradeline"
}

variable "allowed_cidrs" {
  type    = list(string)
  default = ["137.184.174.246/32"]
}
