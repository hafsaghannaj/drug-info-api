# Lab Report: Kubernetes Network Policy Enforcement with Cilium (Zero-Trust Pod Networking)

## Objective
Design, deploy, and validate zero-trust network segmentation in Kubernetes using NetworkPolicies enforced by Cilium.

## Environment
- Platform: kind
- Kubernetes: v1.35.0
- CNI: Cilium v1.18.5
- Runtime: containerd

## Architecture
Namespace: blue-team-apps

Pods:
- good-pod: nginxinc/nginx-unprivileged:stable (TCP 8080)
- nettest: authorized client
- random: unauthorized client

## Policies Implemented
1) default-deny-all
- Denies all ingress and egress for all pods by default.

2) allow-nettest-to-goodpod
- Allows ingress to good-pod from nettest on TCP 8080.

3) allow-nettest-egress
- Allows egress from nettest to:
  - good-pod on TCP 8080
  - kube-dns on UDP/TCP 53

## Validation
Authorized test:
- nettest -> good-pod: ALLOWED

Unauthorized test:
- random -> good-pod: BLOCKED (timeout)

## Conclusion
A default-deny baseline plus explicit allow rules successfully enforced least-privilege pod networking. This prevents unauthorized lateral movement inside the namespace.
