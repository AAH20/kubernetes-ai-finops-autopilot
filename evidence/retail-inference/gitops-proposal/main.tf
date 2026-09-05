# Generated proposal: review before terraform plan/apply
variable "selected_inference_profile" {
  type    = string
  default = "aks-nim-l40s-batched"
}

variable "deployment_mode" {
  type    = string
  default = "shadow"
  validation {
    condition     = contains(["shadow", "canary", "active"], var.deployment_mode)
    error_message = "Mode must be shadow, canary, or active."
  }
}

output "decision_evidence_sha256" {
  value = "55b79e8551c8fcdbc2e5f21271caaac2399d38b20d16435659901102b4fb3de5"
}
