terraform {
  required_providers {
    oci    = { source = "oracle/oci" }
    tls    = { source = "hashicorp/tls" }
    random = { source = "hashicorp/random" }
    http   = { source = "hashicorp/http" }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

data "http" "myip" {
  url = "https://api.ipify.org"
}

locals {
  allowed_cidrs = distinct(concat(["${chomp(data.http.myip.response_body)}/32"], var.allowed_cidrs))
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

data "oci_core_images" "amd" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.E2.1.Micro"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

data "oci_core_images" "arm" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "random_password" "proxy" {
  length  = 24
  special = false
}

resource "oci_core_vcn" "vcn" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "tradeline-proxy-vcn"
}

resource "oci_core_internet_gateway" "ig" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "tradeline-proxy-ig"
}

resource "oci_core_route_table" "rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.vcn.id
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.ig.id
  }
}

resource "oci_core_security_list" "sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.vcn.id

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  dynamic "ingress_security_rules" {
    for_each = local.allowed_cidrs
    content {
      protocol = "6"
      source   = ingress_security_rules.value
      tcp_options {
        min = 22
        max = 22
      }
    }
  }

  dynamic "ingress_security_rules" {
    for_each = local.allowed_cidrs
    content {
      protocol = "6"
      source   = ingress_security_rules.value
      tcp_options {
        min = var.proxy_port
        max = var.proxy_port
      }
    }
  }
}

resource "oci_core_subnet" "subnet" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.vcn.id
  cidr_block        = "10.0.1.0/24"
  route_table_id    = oci_core_route_table.rt.id
  security_list_ids = [oci_core_security_list.sl.id]
  display_name      = "tradeline-proxy-subnet"
}

locals {
  user_data = base64encode(templatefile("${path.module}/cloud-init.tftpl", {
    proxy_port = var.proxy_port
    proxy_user = var.proxy_user
    proxy_pass = random_password.proxy.result
  }))
}

resource "oci_core_instance" "amd" {
  count               = var.amd_count
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[var.ad_index].name
  shape               = "VM.Standard.E2.1.Micro"
  display_name        = "tradeline-proxy-amd-${count.index}"

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.amd.images[0].id
    boot_volume_size_in_gbs = 50
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.subnet.id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = tls_private_key.ssh.public_key_openssh
    user_data           = local.user_data
  }
}

resource "oci_core_instance" "arm" {
  count               = var.arm_count
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[var.ad_index].name
  shape               = "VM.Standard.A1.Flex"
  display_name        = "tradeline-proxy-arm-${count.index}"

  shape_config {
    ocpus         = 1
    memory_in_gbs = 6
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.arm.images[0].id
    boot_volume_size_in_gbs = 50
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.subnet.id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = tls_private_key.ssh.public_key_openssh
    user_data           = local.user_data
  }
}

locals {
  proxy_ips = concat(oci_core_instance.amd[*].public_ip, oci_core_instance.arm[*].public_ip)
}

output "proxy_ips" {
  value = local.proxy_ips
}

output "proxy_pool_csv" {
  value     = join(",", [for ip in local.proxy_ips : "http://${var.proxy_user}:${random_password.proxy.result}@${ip}:${var.proxy_port}"])
  sensitive = true
}

output "ssh_private_key" {
  value     = tls_private_key.ssh.private_key_pem
  sensitive = true
}
