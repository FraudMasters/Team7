# Helm Chart Deployment Testing Guide

This document describes how to test the AgentHR Helm chart deployment on a local Kubernetes cluster.

## Overview

The AgentHR Helm chart provides a production-ready Kubernetes deployment with:
- **Backend API**: FastAPI application with PostgreSQL and Redis
- **Frontend**: React/Vite single-page application
- **Celery Workers**: Asynchronous task processing
- **Celery Beat**: Scheduled task scheduler
- **PostgreSQL**: Database (via Bitnami chart dependency)
- **Redis**: Cache and message broker (via Bitnami chart dependency)
- **Ingress**: Optional nginx ingress for external access
- **Persistent Storage**: PVCs for models, uploads, and backups

## Prerequisites

### Required Tools

1. **Kubernetes Cluster** (one of):
   - minikube: `brew install minikube` or `curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-darwin-amd64`
   - kind: `brew install kind` or `go install sigs.k8s.io/kind@latest`
   - Docker Desktop with Kubernetes enabled
   - GKE, EKS, AKS, or other cloud Kubernetes cluster

2. **Helm 3**:
   ```bash
   brew install helm
   # or
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   ```

3. **kubectl**:
   ```bash
   brew install kubectl
   # or
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
   ```

4. **Docker** (for building images):
   - Docker Desktop: https://www.docker.com/products/docker-desktop

### System Requirements

- **RAM**: Minimum 8GB available for Kubernetes cluster
- **Disk**: At least 20GB free space
- **CPU**: 4+ cores recommended

## Automated Validation

Before deploying to Kubernetes, validate the Helm chart structure:

```bash
bash scripts/test-helm.sh
```

This will check:
- Chart.yaml structure and dependencies
- values.yaml configuration completeness
- Template file existence and syntax
- Deployment, Service, Ingress, and PVC definitions
- ConfigMap and Secrets templates
- Helm best practices

## Manual Testing Procedures

### Setup: Start Local Kubernetes Cluster

#### Option 1: Using minikube

```bash
# Start minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --disk-size=20g

# Enable ingress addon (optional, for ingress testing)
minikube addons enable ingress

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

#### Option 2: Using kind

```bash
# Create a kind cluster
cat <<EOF | kind create cluster --name agenthr --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 8080
  - containerPort: 30443
    hostPort: 8443
EOF

# Verify cluster
kubectl cluster-info --context kind-agenthr
```

#### Option 3: Using Docker Desktop

1. Open Docker Desktop preferences
2. Go to "Kubernetes" tab
3. Check "Enable Kubernetes"
4. Click "Apply & Restart"
5. Wait for Kubernetes to start

### Test 1: Install Helm Chart Dependencies

```bash
# Navigate to project root
cd /path/to/agenthr

# Update Helm dependencies (PostgreSQL and Redis charts)
helm dependency update helm/agenthr

# Verify dependencies downloaded
ls helm/agenthr/charts/
# Should see: postgresql-*.tgz and redis-*.tgz
```

Expected output:
```
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "bitnami" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 2 charts
Downloading postgresql from repo https://charts.bitnami.com/bitnami
Downloading redis from repo https://charts.bitnami.com/bitnami
```

### Test 2: Validate Helm Chart Templates

```bash
# Render templates to verify syntax
helm template agenthr helm/agenthr > /tmp/agenthr-manifests.yaml

# Validate with kubectl (dry-run)
kubectl apply --dry-run=client -f /tmp/agenthr-manifests.yaml

# Check for any template errors
helm lint helm/agenthr
```

Expected output:
```
==> Linting helm/agenthr
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Test 3: Install Helm Chart

```bash
# Create namespace
kubectl create namespace agenthr

# Install the chart
helm install agenthr helm/agenthr \
  --namespace agenthr \
  --set backend.image.tag=latest \
  --set frontend.image.tag=latest \
  --set postgresql.auth.password=postgres123 \
  --set redis.auth.password=redis123 \
  --timeout 10m

# Watch the installation
helm status agenthr -n agenthr
```

Expected output:
```
NAME: agenthr
LAST DEPLOYED: [timestamp]
NAMESPACE: agenthr
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

### Test 4: Wait for Pods to be Ready

```bash
# Watch pod status
kubectl get pods -n agenthr -w

# Wait for all pods to be ready (this may take 3-5 minutes)
kubectl wait --for=condition=ready pod --all -n agenthr --timeout=600s

# Check pod status
kubectl get pods -n agenthr
```

Expected output (all pods should be Running/Completed):
```
NAME                                    READY   STATUS    RESTARTS   AGE
agenthr-backend-xxxxxxxxxx-xxxxx        1/1     Running   0          5m
agenthr-celery-beat-xxxxxxxxxx-xxxxx    1/1     Running   0          5m
agenthr-celery-worker-xxxxxxxxxx-xxxxx  1/1     Running   0          5m
agenthr-frontend-xxxxxxxxxx-xxxxx       1/1     Running   0          5m
agenthr-postgresql-0                    1/1     Running   0          5m
agenthr-redis-master-0                  1/1     Running   0          5m
```

### Test 5: Verify Services

```bash
# List all services
kubectl get svc -n agenthr

# Check service endpoints
kubectl get endpoints -n agenthr
```

Expected output:
```
NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
agenthr-backend           ClusterIP   10.96.xxx.xxx   <none>        8000/TCP   5m
agenthr-frontend          ClusterIP   10.96.xxx.xxx   <none>        5173/TCP   5m
agenthr-postgresql        ClusterIP   10.96.xxx.xxx   <none>        5432/TCP   5m
agenthr-redis-master      ClusterIP   10.96.xxx.xxx   <none>        6379/TCP   5m
```

### Test 6: Port-Forward and Test Backend Health

```bash
# Port-forward to backend service
kubectl port-forward -n agenthr svc/agenthr-backend 8000:8000 &

# Wait a moment for port-forward to establish
sleep 2

# Test backend health endpoint
curl http://localhost:8000/health

# Expected response: {"status":"healthy"} or similar
```

Expected health check response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

Stop port-forward:
```bash
# Kill the background port-forward process
pkill -f "port-forward.*svc/agenthr-backend"
```

### Test 7: Port-Forward and Test Frontend

```bash
# Port-forward to frontend service
kubectl port-forward -n agenthr svc/agenthr-frontend 5173:5173 &

# Wait for port-forward
sleep 2

# Test frontend (should return HTML)
curl http://localhost:5173/ | head -20

# Or open in browser
open http://localhost:5173
```

Expected: HTML page with React application loads successfully.

Stop port-forward:
```bash
pkill -f "port-forward.*svc/agenthr-frontend"
```

### Test 8: Check Pod Logs

```bash
# Backend logs
kubectl logs -n agenthr -l app.kubernetes.io/component=backend --tail=50

# Frontend logs
kubectl logs -n agenthr -l app.kubernetes.io/component=frontend --tail=50

# Celery worker logs
kubectl logs -n agenthr -l app.kubernetes.io/component=celery-worker --tail=50

# PostgreSQL logs
kubectl logs -n agenthr -l app.kubernetes.io/name=postgresql --tail=50

# Redis logs
kubectl logs -n agenthr -l app.kubernetes.io/name=redis --tail=50
```

Check for:
- No error messages
- Successful database connections
- Services starting successfully
- No crash loops

### Test 9: Verify Persistent Volumes

```bash
# List persistent volume claims
kubectl get pvc -n agenthr

# Check persistent volumes
kubectl get pv
```

Expected output:
```
NAME                          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
agenthr-models-cache          Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   20Gi       RWO            standard       5m
agenthr-uploads               Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   10Gi       RWO            standard       5m
agenthr-backups               Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   50Gi       RWO            standard       5m
data-agenthr-postgresql-0     Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   8Gi        RWO            standard       5m
redis-data-agenthr-redis-master-0  Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   8Gi        RWO            standard       5m
```

### Test 10: Test Helm Chart Upgrade

```bash
# Modify a value in values.yaml or use --set
helm upgrade agenthr helm/agenthr \
  --namespace agenthr \
  --set backend.replicaCount=2 \
  --set frontend.replicaCount=2

# Watch the rolling update
kubectl get pods -n agenthr -w

# Verify upgrade
helm list -n agenthr
# Should show REVISION: 2
```

### Test 11: Helm Test (Optional)

If test hooks are defined in the chart:

```bash
# Run Helm tests
helm test agenthr -n agenthr

# Check test results
kubectl get pods -n agenthr | grep test
```

### Test 12: Helm Rollback

```bash
# Rollback to previous revision
helm rollback agenthr -n agenthr

# Verify rollback
helm list -n agenthr
# Should show REVISION: 3 (rollback creates new revision)

# Check pods rolled back
kubectl get pods -n agenthr
```

### Test 13: Uninstall and Verify Cleanup

```bash
# Uninstall the release
helm uninstall agenthr -n agenthr

# Verify pods are terminated
kubectl get pods -n agenthr
# Should show: No resources found

# Check PVCs (may still exist depending on retention policy)
kubectl get pvc -n agenthr

# Delete PVCs if they still exist
kubectl delete pvc --all -n agenthr

# Delete namespace
kubectl delete namespace agenthr

# Verify cleanup
kubectl get all -n agenthr 2>&1 | grep "No resources found"
```

## Advanced Testing Scenarios

### Scenario 1: Test with Ingress Enabled

```bash
# Install with ingress enabled
helm install agenthr helm/agenthr \
  --namespace agenthr \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=agenthr.local \
  --set ingress.hosts[0].paths[0].path=/ \
  --set ingress.hosts[0].paths[0].pathType=Prefix

# Add to /etc/hosts (for minikube)
echo "$(minikube ip) agenthr.local" | sudo tee -a /etc/hosts

# Test ingress
curl http://agenthr.local/
curl http://agenthr.local/api/health
```

### Scenario 2: Test with Autoscaling

```bash
# Install with autoscaling enabled
helm install agenthr helm/agenthr \
  --namespace agenthr \
  --set backend.autoscaling.enabled=true \
  --set backend.autoscaling.minReplicas=2 \
  --set backend.autoscaling.maxReplicas=5

# Check HPA
kubectl get hpa -n agenthr

# Generate load to trigger autoscaling
kubectl run -it --rm load-generator --image=busybox --restart=Never -- sh -c "while true; do wget -q -O- http://agenthr-backend:8000/health; done"

# Watch scaling (in another terminal)
kubectl get hpa -n agenthr -w
```

### Scenario 3: Test with Custom Values

Create a custom values file:

```bash
cat > custom-values.yaml <<EOF
backend:
  replicaCount: 3
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi

frontend:
  replicaCount: 2

postgresql:
  primary:
    persistence:
      size: 20Gi

redis:
  master:
    persistence:
      size: 4Gi

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: agenthr.example.com
      paths:
        - path: /
          pathType: Prefix
EOF

# Install with custom values
helm install agenthr helm/agenthr \
  --namespace agenthr \
  -f custom-values.yaml
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status and events
kubectl describe pod <pod-name> -n agenthr

# Check logs
kubectl logs <pod-name> -n agenthr

# Common issues:
# - Image pull errors: Check image tags and registry access
# - Resource limits: Ensure cluster has enough CPU/memory
# - PVC binding: Check storage class availability
```

### Database Connection Errors

```bash
# Check PostgreSQL pod
kubectl logs -n agenthr -l app.kubernetes.io/name=postgresql

# Check database credentials in secrets
kubectl get secret agenthr-secrets -n agenthr -o yaml

# Test database connection from backend pod
kubectl exec -it -n agenthr <backend-pod> -- psql -h agenthr-postgresql -U postgres
```

### Redis Connection Errors

```bash
# Check Redis pod
kubectl logs -n agenthr -l app.kubernetes.io/name=redis

# Test Redis connection
kubectl exec -it -n agenthr <backend-pod> -- redis-cli -h agenthr-redis-master ping
```

### PVC Not Binding

```bash
# Check PVC status
kubectl get pvc -n agenthr
kubectl describe pvc <pvc-name> -n agenthr

# Check available storage classes
kubectl get storageclass

# For minikube, ensure default storage class exists:
kubectl get storageclass
# Should see 'standard (default)'
```

### Helm Install Timeout

```bash
# Increase timeout
helm install agenthr helm/agenthr \
  --namespace agenthr \
  --timeout 15m

# Or check what's taking long
kubectl get pods -n agenthr -w
kubectl describe pod <slow-pod> -n agenthr
```

### Image Pull Errors

```bash
# If using local images with minikube
eval $(minikube docker-env)
docker build -t agenthr/backend:latest ./backend
docker build -t agenthr/frontend:latest ./frontend

# Or set image pull policy
helm install agenthr helm/agenthr \
  --set backend.image.pullPolicy=Never \
  --set frontend.image.pullPolicy=Never
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Helm Chart

on: [push, pull_request]

jobs:
  helm-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Helm
        uses: azure/setup-helm@v3
        with:
          version: '3.11.0'

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Create kind cluster
        uses: helm/kind-action@v1.5.0

      - name: Install Helm dependencies
        run: helm dependency update helm/agenthr

      - name: Lint Helm chart
        run: helm lint helm/agenthr

      - name: Install Helm chart
        run: |
          helm install agenthr helm/agenthr \
            --wait \
            --timeout 10m \
            --set postgresql.auth.password=test123 \
            --set redis.auth.password=test123

      - name: Test deployment
        run: |
          kubectl get pods
          kubectl wait --for=condition=ready pod --all --timeout=300s
          kubectl get all
```

## Performance Considerations

### Resource Allocation

Recommended resources for production:

```yaml
backend:
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 2000m
      memory: 4Gi

celery-worker:
  resources:
    limits:
      cpu: 6000m
      memory: 12Gi
    requests:
      cpu: 3000m
      memory: 6Gi

postgresql:
  primary:
    resources:
      limits:
        cpu: 2000m
        memory: 4Gi
      requests:
        cpu: 1000m
        memory: 2Gi
```

### Scaling Guidelines

- **Backend**: Scale horizontally based on API request rate
- **Celery Workers**: Scale based on queue depth and task processing time
- **Frontend**: Scale for redundancy (2-3 replicas minimum)
- **Database**: Consider read replicas for high read workloads

## Best Practices

1. **Use Namespaces**: Always deploy to a dedicated namespace
2. **Set Resource Limits**: Prevent resource exhaustion
3. **Enable Monitoring**: Use Prometheus and Grafana for observability
4. **Backup Strategy**: Configure automated database backups
5. **Health Checks**: Ensure all deployments have proper probes
6. **Rolling Updates**: Use maxUnavailable and maxSurge for zero-downtime deploys
7. **Secrets Management**: Use Kubernetes secrets or external secret stores
8. **Version Control**: Pin chart versions and image tags

## Clean Up

After testing, clean up the local cluster:

```bash
# For minikube
minikube stop
minikube delete

# For kind
kind delete cluster --name agenthr

# For Docker Desktop
# Just disable Kubernetes in preferences
```

## Next Steps

After successful testing:

1. **Production Deployment**: Deploy to production Kubernetes cluster
2. **Monitoring**: Set up Prometheus and Grafana
3. **Logging**: Configure centralized logging (ELK, Loki)
4. **CI/CD**: Integrate Helm deployment into CI/CD pipeline
5. **Documentation**: Update production deployment docs
6. **Backups**: Configure automated database backups
7. **Disaster Recovery**: Test backup/restore procedures

## Additional Resources

- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Bitnami PostgreSQL Chart](https://github.com/bitnami/charts/tree/main/bitnami/postgresql)
- [Bitnami Redis Chart](https://github.com/bitnami/charts/tree/main/bitnami/redis)
- AgentHR Helm Chart README: `helm/agenthr/README.md`
