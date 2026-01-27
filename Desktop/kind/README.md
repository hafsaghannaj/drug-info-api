# Kubernetes NetworkPolicy Enforcement Lab (Cilium + kind)

## Overview

This lab demonstrates zero-trust pod networking in Kubernetes using NetworkPolicy enforcement with Cilium. The objective is to prevent unauthorized lateral movement within a namespace while allowing only explicitly approved communication paths.

Both allowed and denied traffic paths are validated using live network tests, and evidence is preserved in a format suitable for security review or audit.

---

## Attack Scenario Simulated

This lab simulates a compromised workload attempting lateral movement inside a Kubernetes namespace.

* **random** represents an untrusted or compromised pod
* **good-pod** represents a target application service
* **nettest** represents an explicitly authorized client

The goal is to ensure that only approved communication paths are possible, even when all pods share the same namespace.

---

## Threat Model

* Prevent lateral movement between application pods within the same namespace
* Enforce least-privilege network access
* Require explicit authorization for all pod-to-pod communication
* Ensure required dependencies (such as DNS) are narrowly permitted

### Out of Scope

* North–south ingress from outside the cluster
* Service mesh or L7 (HTTP-aware) policy enforcement
* Encryption in transit
* Identity-based authorization using ServiceAccounts

---

## Environment

* Kubernetes: v1.35.0 (kind)
* CNI: Cilium v1.18.5 (NetworkPolicy enforcement enabled)
* Container runtime: containerd

**Note:** Kubernetes NetworkPolicies are only enforced when a compatible CNI is installed. kind’s default CNI does not enforce NetworkPolicy. This lab explicitly installs Cilium to ensure enforcement.

---

## Namespace

* **blue-team-apps**

All pods and NetworkPolicies are scoped to this namespace to simulate realistic multi-workload environments.

---

## Pods

| Pod      | Purpose                               | Security Context                                       |
| -------- | ------------------------------------- | ------------------------------------------------------ |
| good-pod | Unprivileged NGINX server (TCP 8080)  | Non-root, seccomp RuntimeDefault, capabilities dropped |
| nettest  | Authorized client used for validation | Non-root, seccomp RuntimeDefault, capabilities dropped |
| random   | Unauthorized client                   | Non-root, seccomp RuntimeDefault, capabilities dropped |

All containers run without privilege escalation and follow Kubernetes Pod Security Restricted standards.

---

## Network Policies

### 1. default-deny-all

* Applies to all pods in the namespace
* Denies all ingress and egress traffic by default
* Establishes a zero-trust networking baseline

---

### 2. allow-nettest-to-goodpod

* Allows ingress to **good-pod** on TCP port 8080
* Source restricted to pods labeled `app=nettest`
* No other pods may initiate connections to good-pod

---

### 3. allow-nettest-egress

* Allows egress from **nettest** to:

  * **good-pod** on TCP port 8080
  * **kube-dns** in the `kube-system` namespace on TCP/UDP port 53

#### DNS Consideration

When enforcing default-deny egress, DNS traffic must be explicitly allowed. Without this, name resolution failures may appear as application connectivity issues.

DNS access is restricted to kube-dns only, preserving least-privilege principles.

---

## Validation Results

### Authorized Path

* **nettest → good-pod (TCP 8080): ALLOWED**

### Unauthorized Path

* **random → good-pod (TCP 8080): BLOCKED (timeout)**

These results confirm correct enforcement of least-privilege pod networking and prevention of lateral movement.

---

## Evidence

All supporting artifacts are stored under:

```
~/Desktop/kind/
```

Including:

* `pods.txt` (pod state and labels)
* `networkpolicies.yaml` and `networkpolicies.txt`
* Individual NetworkPolicy descriptions
* Connectivity test outputs (ALLOWED / BLOCKED)
* Aggregated proof file

All validation was performed using live `kubectl exec` network tests.

---

## Limitations

* NetworkPolicies do not provide encryption in transit
* Policies do not protect against compromised pods with valid network permissions
* North–south traffic is not addressed
* No L7 (HTTP-aware) filtering is implemented

---

## Conclusion

This lab demonstrates effective enforcement of zero-trust networking in Kubernetes using NetworkPolicies backed by a policy-aware CNI. A default-deny baseline combined with explicit allow rules successfully prevents unauthorized lateral movement while preserving required application functionality.

This approach reflects real-world Kubernetes security controls used to reduce blast radius in multi-tenant or production environments.
