<p align="center">
 <img src="docs/assets/sibyl-icon.png" alt="drawing" width="200"/>
</p>

# Sibyl
> Watch for error events, fetch logs from the problem pod, post em to slack. Simple as that

[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/sibyl)](https://artifacthub.io/packages/helm/sibyl/sibyl)

![Python Version](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fraw.githubusercontent.com%2Fbensoer%2Fsibyl%2Frefs%2Fheads%2Fmain%2F.python-version&search=.*&logo=python&logoColor=blue&label=python&color=yellow)
![Latest Container](https://img.shields.io/github/v/release/bensoer/sibyl?sort=semver&filter=v*&logo=docker&label=Latest%20Container&color=blue)
![Latest Chart](https://img.shields.io/github/v/release/bensoer/sibyl?sort=semver&filter=!v&logo=helm&label=Latest%20Chart&color=green&logoColor=green)


Sibyl allows you to send Kubernetes error alerts with log context to slack!


# Setup
To deploy Sibyl, you need to create a Slack App connected to your workspace where you would like to receive alerts, and then you need to deploy Sibyl into the target Kubernetes cluster that you would like to receive alerts from.

## Create The Slack App
1. Go to Slack Apps, login and on the top right select "Create New App": https://api.slack.com/apps 
2. On the popup select "From Manifest"
3. Select your workspace
4. Flip to the YAML tab, and then upload the manifest located in this repository at: [docs/sibyl-slack-manifest.yml](docs/sibyl-slack-manifest.yml)
5. One created, select Settings > Basic Information and scroll down to the "Display Information" section. Select "Add App Icon"
6. Upload the Sibyl icon located in this repository at: [docs/assets/sibyl-icon.png](docs/assets/sibyl-icon.png)
7. Then go to Settings > Install App and select "Install App To Workspace"
8. Follow the screens and prompts. Note the slack channel you choose, you will need this when you install Sibyl
9. Once complete, go back to Settings > Install App and copy the "Bot User OAuth Token". You will need this when you install Sibyl


## Install Sibyl Into Your Cluster

Install with Helm by running:

```bash
# Add The Repository
helm repo add sibyl https://bensoer.github.io/sibyl
# Install the chart
helm upgrade --install sibyl sibyl/sibyl --set slack.channel=<YOUR_SLACK_CHANNEL> --set slack.botToken=<BOT_TOKEN>
```

Set `YOUR_SLACK_CHANNEL` to the channel your selected in step 8 when you installed Sibyl slack app in your workspace

Set `BOT_TOKEN` to the "Bot User OAuth Token" on the Settings > Install App page of your Sibyl Slack App

# Configuration
Sibyl comes with a handful of configurations you can modify in the project.

| Variable | Description | Required | Default Value / Possible Values |
| -------- | ----------- | -------- | ------------------------------- |
| `SLACK_BOT_TOKEN` | Slack App Bot Auth Token | TRUE | N/A |
| `SLACK_CHANNEL` | Slack Channel To Post Alerts To | TRUE | Both `#mychannelname` and `mychannelname` formats are accepted |
| `LOG_LEVEL` | Set the log output level. `DEBUG` will output log from depednency libraries as well | FALSE | Default: `INFO`. Options: `INFO`, `DEBUG`, `WARNING`, `ERROR` |
| `HEALTH_CHECK_PORT` | Set the port to listen for health checks. You will need to update the Helm chart to match this value if changed | FALSE | 8080

The above configurations are passed to Sibyl, and read at startup, via  environment variables. The `SLACK_BOT_TOKEN` and `SLACK_CHANNEL` variables are the only ones that have been mapped out into helm values though.

To modify the other settings you will need to do the following:

1. Create a secret within your cluster called `sibyl-env-configuration` containing keys that match each environment variable and the values to the setting you want. Example:
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
    name: sibyl-env-credentials
    stringData:
        LOG_LEVEL: DEBUG
    ```
2. Apply this secret into the same namespace as sibyl is deployed
3. Deploy the helm chart with its `envFrom` values pointing at the configuration secret:
    ```bash
    helm upgrade --install sibyl sibyl/sibyl --set slack.channel=<YOUR_SLACK_CHANNEL> --set slack.botToken=<BOT_TOKEN>
    --set envFrom[0].secretRef.name=sibyl-env-credentials
    ```
    Alternatively, make a copy of the `values.yaml` file and apply these changes and deploy it like this (assuming you set `slack.channel` and `slack.botToken` within it as well)
    ```bash
    helm upgrade --install sibyl sibyl/sibyl --values=./yourvaluesfile.yaml
    ```
4. If the deployment does not restart Sibyl, give it a restart through kubectl:
    ```bash
    kubectl rollout restart deployment sibyl
    ```


# Future Features
- Multi-cluster support
    - Include the cluster name in the alerts so that multiple sibyls can use the same slack app
- Remove headers from the table ? Kinda useless extra information, the rows give enough context


# Developer Notes
Install development onto minikube by running:

```bash
helm upgrade --install sibyl charts/sibyl --set image.tag=main --set image.pullPolicy=Always
```