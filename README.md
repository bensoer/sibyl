<p align="center">
 <img src="docs/assets/sibyl-icon.png" alt="drawing" width="200"/>
</p>

# Sibyl
> Watch for error events, fetch logs from the problem pod, post em to slack. Simple as that

Sibyl allows you to send Kubernetes error alerts with log context to slack!


# Install
Install with Helm by running:



# Development Setup
Install development onto minikube by running:

```bash
helm upgrade --install sibyl charts/sibyl --set image.tag=main --set image.pullPolicy=Always
```