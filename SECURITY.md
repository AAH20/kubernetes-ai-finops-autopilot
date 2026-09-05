# Security policy

Do not place cloud credentials, customer identifiers, prompts, model outputs, revenue data, internal endpoints or production telemetry in public fixtures or issues.

The current engine is read-only and requires no Kubernetes or cloud credential. Generated Terraform and Helm values are proposals only. Review policy, identity, network, residency, availability and rollback implications before deployment.

Production collectors should use workload identity and least-privilege read access. Production executors should be separate, short-lived, policy-gated, auditable, and unable to promote a canary without explicit authorization.

Report vulnerabilities privately through GitHub Security Advisories with a sanitized reproduction and affected version.
