# Monitoring and Alerting

This directory contains all monitoring, logging, and alerting configuration for the Resume Analysis application.

## Overview

The monitoring stack consists of:
- **Grafana**: Visualization dashboards and alert management (http://localhost:3001)
- **Prometheus**: Metrics collection and storage (http://localhost:9090)
- **Loki**: Log aggregation (http://localhost:3100)
- **Promtail**: Log collection agent
- **PostgreSQL Exporter**: Database metrics
- **Celery Exporter**: Task queue metrics

## Quick Start

1. Start the monitoring stack:
```bash
docker-compose up -d
```

2. Access Grafana:
   - URL: http://localhost:3001
   - Default credentials: `admin` / `admin` (change on first login)

## Configuring Alert Notifications

### Email Alerts

To enable email notifications, configure the following environment variables in your `.env` file:

```bash
# SMTP Configuration
GRAFANA_SMTP_HOST=smtp.gmail.com:587
GRAFANA_SMTP_USER=your_email@gmail.com
GRAFANA_SMTP_PASSWORD=your_app_password
GRAFANA_SMTP_FROM_ADDRESS=grafana@yourdomain.com

# Alert Recipient
ALERT_EMAIL_ADDRESS=alerts@example.com
```

**Common SMTP Providers:**

#### Gmail
```bash
GRAFANA_SMTP_HOST=smtp.gmail.com:587
GRAFANA_SMTP_USER=your_email@gmail.com
GRAFANA_SMTP_PASSWORD=your_app_password  # Use an App Password, not your account password
```

To create an App Password for Gmail:
1. Go to Google Account settings
2. Enable 2-Step Verification
3. Go to Security → App Passwords
4. Generate a new app password for "Mail"

#### Outlook/Office365
```bash
GRAFANA_SMTP_HOST=smtp.office365.com:587
GRAFANA_SMTP_USER=your_email@outlook.com
GRAFANA_SMTP_PASSWORD=your_password
```

#### SendGrid
```bash
GRAFANA_SMTP_HOST=smtp.sendgrid.net:587
GRAFANA_SMTP_USER=apikey
GRAFANA_SMTP_PASSWORD=SG.your_api_key
```

### Webhook Alerts

Webhook alerts can send notifications to:
- Slack
- Microsoft Teams
- Discord
- Any custom webhook endpoint

Configure in your `.env` file:

```bash
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Slack Webhook Setup

1. Create a Slack app at https://api.slack.com/apps
2. Enable "Incoming Webhooks"
3. Create a new webhook for your workspace
4. Copy the webhook URL to `ALERT_WEBHOOK_URL`

#### Microsoft Teams Setup

1. Go to your Teams channel
2. Click "..." → "Connectors"
3. Search for "Incoming Webhook"
4. Configure and copy the webhook URL

#### Discord Setup

1. Go to Server Settings → Integrations
2. Create a new webhook
3. Copy the webhook URL

### Testing Notifications

After configuration:

1. Restart Grafana:
```bash
docker-compose restart grafana
```

2. Access Grafana at http://localhost:3001/alerting/notifications

3. Test your notification channels:
   - Click the contact point (e.g., "email-alerts" or "webhook-alerts")
   - Click "Send test notification"
   - Verify you receive the test alert

## Alert Rules

Alerts are configured in `grafana/provisioning/alerts/alert_rules.yml` and include:

### API Performance Alerts
- **HighAPIErrorRate**: API error rate > 5% (warning)
- **CriticalAPIErrorRate**: API error rate > 15% (critical)
- **HighAPILatency**: P95 latency > 2s (warning)
- **CriticalAPILatency**: P95 latency > 5s (critical)

### Celery Task Alerts
- **CeleryQueueBackup**: Queue depth > 100 tasks (warning)
- **CriticalCeleryQueueBackup**: Queue depth > 500 tasks (critical)
- **HighCeleryTaskFailureRate**: Failure rate > 10% (warning)
- **CriticalCeleryTaskFailureRate**: Failure rate > 25% (critical)
- **CeleryWorkersDown**: No workers running (critical)
- **SlowCeleryTasks**: P95 runtime > 300s (warning)

### ML Inference Alerts
- **SlowMLInference**: P95 inference time > 30s (warning)
- **CriticalMLInference**: P95 inference time > 60s (critical)

### Database Alerts
- **SlowDatabaseQueries**: P95 query duration > 1s (warning)
- **CriticalDatabaseQueries**: P95 query duration > 3s (critical)

### System Alerts
- **ServiceDown**: Service is unreachable (critical)
- **HighMemoryUsage**: Memory usage > 90% (warning)

## Dashboards

Pre-configured dashboards are available in Grafana for:
- API performance metrics
- Celery task monitoring
- Database performance
- System resource usage
- ML model inference metrics

Access them at: http://localhost:3001/dashboards

## Troubleshooting

### Notifications Not Working

1. Check Grafana logs:
```bash
docker-compose logs grafana | grep -i smtp
docker-compose logs grafana | grep -i alert
```

2. Verify SMTP configuration in Grafana:
   - Go to Configuration → Alerting → Contact points
   - Check the contact point configuration
   - Send a test notification

3. Common issues:
   - **Gmail**: Use an App Password, not your account password
   - **Firewall**: Ensure SMTP port (587) is not blocked
   - **Webhook**: Verify the URL is accessible from the container

### Alert Rules Not Firing

1. Check if Prometheus is scraping metrics:
   http://localhost:9090/targets

2. Verify alert rules in Prometheus:
   http://localhost:9090/alerts

3. Check Grafana alert configuration:
   - Go to Alerting → Alert rules
   - Verify rules are present and have data

## Configuration Files

- `grafana/provisioning/datasources/datasources.yml`: Prometheus and Loki data sources
- `grafana/provisioning/alerts/alert_rules.yml`: Alert rule definitions
- `grafana/provisioning/alerting/contactpoints.yml`: Email and webhook notification channels
- `prometheus/prometheus.yml`: Prometheus scrape configuration
- `loki/config.yml`: Loki log storage configuration
- `promtail/config.yml`: Log collection configuration

## Maintenance

### View Logs

All services logs:
```bash
docker-compose logs -f
```

Specific service:
```bash
docker-compose logs -f grafana
```

### Backup Grafana Data

Grafana dashboards and configurations are stored in a Docker volume. To backup:

```bash
docker run --rm -v resume_analysis_grafana_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup.tar.gz -C /data .
```

### Update Monitoring Stack

1. Pull latest images:
```bash
docker-compose pull
```

2. Restart services:
```bash
docker-compose up -d
```

## Security Notes

1. **Change default credentials**: Update `GRAFANA_USER` and `GRAFANA_PASSWORD` in `.env`
2. **Use App Passwords**: For Gmail, always use App Passwords, not your main password
3. **Secure webhooks**: Webhook URLs contain sensitive tokens - don't commit them to git
4. **TLS**: SMTP uses STARTTLS for secure communication
5. **Firewall**: Consider restricting Grafana access in production environments

## Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
