# Sibyl
> Watch for error events, fetch logs from the problem pod, post em to slack. Simple as that

This chart bootstraps a [Sibyl](https://github.com/bensoer/sibyl) deployment on a
[Kubernetes](http://kubernetes.io) cluster using the [Helm](https://helm.sh)
package manager.

## Introduction

Sibyl is a Kubernetes operator that watches for error events in a cluster, fetches logs from the pod that is experiencing issues, and forwards them to a configured Slack channel. This provides a simple and effective way to get real-time alerts with context for failures in your cluster.

## Prerequisites

*   Kubernetes 1.15+
*   Helm 3.2.0+
*   A Slack App created in your workspace. You can find instructions on how to create one [here](https://github.com/bensoer/sibyl#create-the-slack-app).

## Installing the Chart

To install the chart with the release name `my-release`:

```bash
# Add The Repository
helm repo add sibyl https://bensoer.github.io/sibyl
# Install the chart
helm upgrade --install sibyl sibyl/sibyl --set slack.channel=<YOUR_SLACK_CHANNEL> --set slack.botToken=<BOT_TOKEN>
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
| `image.tag` | The image tag to use. Defaults to the chart's appVersion. | `""` |
| `image.pullPolicy` | Image pull policy. | `IfNotPresent` |
| `imagePullSecrets` | Secrets for pulling images from a private repository. | `[]` |
| `nameOverride` | Override the chart name. | `""` |
| `fullnameOverride` | Override the full name of the release. | `""` |
| `slack.channel` | The channel name Sibyl sends notifications to. NOTE: Sibyl must be invited to the channel | `""` |
| `slack.botToken` | Bot token for Sibyl to authenticate with Slack API | `""` |
| `slack.useExistingSecret.enabled` | Use an existing secret for slack credetnials. If enabled the `channel` and `botToken` values are ignored. | `false` |
| `slack.useExistingSecret.secretRef.name` | The name of the existing secret to use for slack credentials. | `""` |
| `clusterName` | Optional cluster name to uniquely identify this instance of Sibyl when sending notications. Useful if you have multiple Sibyl instances sending notifications to the same slack app | `null` |
| `podLogTailLines` | Number of lines to fetch from problem pods for notications. Slack snippet max size is 1MB so be careful increasing this too much. | `100` |
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
| `envFrom` | Additional environment variables from secrets or configmaps. | `[]` |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example:

```bash
helm install my-release . --set replicaCount=2
```

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example:

```bash
helm install my-release . -f values.yaml
```
