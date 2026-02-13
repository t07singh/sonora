# Sonora Platform Deployment Guide

## Quick Start (Local Development)

### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)

### Single Command Deployment

```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd sonora

# Start all services with a single command
docker compose up --build
```

This will start:
- **API Backend** (FastAPI) - Internal port 8000
- **UI Dashboard** (Streamlit) - Internal port 8501  
- **Redis Cache** - Internal port 6379
- **Nginx Reverse Proxy** - Public ports 80/443
- **Prometheus** - Internal port 9090
- **Grafana** - Internal port 3000

### Access Points

After running `docker compose up --build`, access the platform at:

- **Dashboard**: http://localhost/dashboard/ (Streamlit UI)
- **API Root**: http://localhost/api/ (FastAPI)
- **Health Check**: http://localhost/health
- **WebSocket**: ws://localhost/ws/status
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/sonora_admin_pw)

## Production Deployment

### Environment Variables

Create a `.env` file for production:

```bash
# API Configuration
REDIS_URL=redis://redis:6379/0
PROMETHEUS_METRICS_PATH=/metrics
LOG_LEVEL=INFO

# UI Configuration  
API_BASE=http://api:8000
WS_BASE=ws://api:8000

# Grafana
GF_SECURITY_ADMIN_PASSWORD=your_secure_password

# SSL Configuration (optional)
SSL_CERT_PATH=/etc/nginx/certs/cert.pem
SSL_KEY_PATH=/etc/nginx/certs/key.pem
```

### SSL/HTTPS Setup

1. **Generate SSL certificates** (for production):
```bash
# Create self-signed certificate for testing
mkdir -p deploy/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout deploy/certs/key.pem \
    -out deploy/certs/cert.pem
```

2. **Enable HTTPS** in `deploy/nginx.conf`:
   - Uncomment the HTTPS server block
   - Update certificate paths if needed

### Cloud Deployment

#### AWS ECS/Fargate

```bash
# Build and push images
docker build -f Dockerfile.backend -t your-registry/sonora-api:latest .
docker build -f ui/Dockerfile.ui -t your-registry/sonora-ui:latest .

# Push to registry
docker push your-registry/sonora-api:latest
docker push your-registry/sonora-ui:latest
```

#### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy sonora-api --source . --platform managed --region us-central1
gcloud run deploy sonora-ui --source ui --platform managed --region us-central1
```

#### Azure Container Instances

```bash
# Create resource group
az group create --name sonora-rg --location eastus

# Deploy containers
az container create --resource-group sonora-rg --name sonora-api --image your-registry/sonora-api:latest
az container create --resource-group sonora-rg --name sonora-ui --image your-registry/sonora-ui:latest
```

### Kubernetes Deployment

Create `k8s/` directory with:

- `namespace.yaml` - Kubernetes namespace
- `configmap.yaml` - Configuration
- `secrets.yaml` - Sensitive data
- `deployment.yaml` - Application deployments
- `service.yaml` - Services
- `ingress.yaml` - Ingress controller

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

## Monitoring & Observability

### Prometheus Metrics

The platform exposes metrics at `/metrics`:

- `sonora_requests_total` - Total API requests
- `sonora_request_duration_seconds` - Request latency
- `sonora_active_connections` - WebSocket connections
- `sonora_cache_hits_total` - Cache hit rate
- `sonora_system_cpu_percent` - CPU usage
- `sonora_system_memory_percent` - Memory usage

### Grafana Dashboards

Access Grafana at `/grafana/` with:
- Username: `admin`
- Password: `sonora_admin_pw` (change in production)

### Health Checks

- **API Health**: `GET /health`
- **Cache Status**: `GET /api/cache/stats`
- **System Status**: `GET /api/status`

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 80, 443, 3000, 8000, 8501, 9090 are available
2. **Redis connection**: Check Redis container is running and accessible
3. **WebSocket issues**: Verify nginx proxy configuration for WebSocket support

### Logs

```bash
# View all logs
docker compose logs

# View specific service logs
docker compose logs api
docker compose logs ui
docker compose logs nginx
```

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG docker compose up
```

## Scaling

### Horizontal Scaling

```bash
# Scale API instances
docker compose up --scale api=3

# Scale UI instances  
docker compose up --scale ui=2
```

### Load Balancing

Update `deploy/nginx.conf` upstream blocks:

```nginx
upstream api {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}
```

## Security

### Production Security Checklist

- [ ] Change default passwords
- [ ] Enable HTTPS with valid certificates
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable security headers
- [ ] Regular security updates
- [ ] Monitor access logs

### Network Security

```bash
# Create custom network
docker network create sonora-network

# Update docker-compose.yml to use custom network
networks:
  sonora-network:
    external: true
```

## Backup & Recovery

### Redis Data Backup

```bash
# Backup Redis data
docker exec sonora_redis redis-cli BGSAVE
docker cp sonora_redis:/data/dump.rdb ./backup/
```

### Configuration Backup

```bash
# Backup configuration files
tar -czf sonora-config-backup.tar.gz deploy/ docker-compose.yml
```

## Performance Tuning

### Redis Optimization

```bash
# Redis configuration in docker-compose.yml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Nginx Optimization

```nginx
# Add to nginx.conf
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
gzip on;
gzip_types text/plain application/json;
```

## Support

For issues and questions:
- Check logs: `docker compose logs`
- Health checks: `curl http://localhost/health`
- Metrics: `curl http://localhost/metrics`
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
