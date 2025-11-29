# Sibyl

This chart bootstraps a [Sibyl](https://github.com/bensoer/sibyl) deployment on a
[Kubernetes](http://kubernetes.io) cluster using the [Helm](https://helm.sh)
package manager.

## Introduction

Sibyl is a Kubernetes operator that watches for error events in a cluster, fetches logs from the pod that is experiencing issues, and forwards them to a configured Slack channel. This provides a simple and effective way to get real-time alerts with context for failures in your cluster.

## Prerequisites

*   Kubernetes 1.15+
*   Helm 3.2.0+

## Installing the Chart

To install the chart with the release name `my-release`:

```bash
helm install my-release .
```

The command deploys Sibyl on the Kubernetes cluster in the default configuration. The [configuration](#configuration) section lists the parameters that can be configured during installation.

## Uninstalling the Chart

To uninstall/delete the `my-release` deployment:

```bash
helm delete my-release
```

The command removes all the Kubernetes components associated with the chart and deletes the release.

## Configuration

The following table lists the configurable parameters of the Sibyl chart and their default values.

| Parameter | Description | Default |
| --- | --- | --- |
| `replicaCount` | Number of replicas to deploy. | `1` |
| `image.pullPolicy` | Image pull policy. | `IfNotPresent` |
| `imagePullSecrets` | Secrets for pulling images from a private repository. | `[]` |
| `nameOverride` | Override the chart name. | `""` |
| `fullnameOverride` | Override the full name of the release. | `""` |
| `serviceAccount.create` | Whether to create a service account. | `true` |
| `serviceAccount.automount` | Automount ServiceAccount's API credentials. | `true` |
| `serviceAccount.annotations` | Annotations to add to the service account. | `{}` |
| `serviceAccount.name` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template. | `""` |
| `podAnnotations` | Annotations to add to the pod. | `{}` |
| `podLabels` | Labels to add to the pod. | `{}` |
| `podSecurityContext` | Pod security context. | `{}` |
| `securityContext` | Security context. | `{}` |
| `resources` | Resources for the container. | `{}` |
| `livenessProbe` | Liveness probe configuration. | See `values.yaml` |
| `readinessProbe` | Readiness probe configuration. | See `values.yaml` |
| `volumes` | Additional volumes. | `[]` |
| `volumeMounts` | Additional volume mounts. | `[]` |
| `nodeSelector` | Node selector. | `{}` |
| `tolerations` | Tolerations. | `[]` |
| `affinity` | Affinity. | `{}` |
| `envFrom` | Additional environment variables from secrets or configmaps. | `{}` |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example:

```bash
helm install my-release . --set replicaCount=2
```

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example:

```bash
helm install my-release . -f values.yaml
```