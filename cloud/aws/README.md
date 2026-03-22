# AgentHR AWS Marketplace Deployment

This directory contains the CloudFormation template for deploying AgentHR on AWS through the AWS Marketplace or manual deployment.

## Overview

The CloudFormation template (`marketplace.yaml`) provisions a complete, production-ready infrastructure for AgentHR, including:

- **Compute**: EC2 instance running Docker containers
- **Database**: RDS PostgreSQL 14 with Multi-AZ deployment
- **Cache**: ElastiCache Redis cluster with automatic failover
- **Networking**: VPC with public/private subnets, NAT Gateway, and Application Load Balancer
- **Storage**: S3 bucket for backups with lifecycle policies
- **Security**: Security groups, encrypted storage, Secrets Manager
- **Monitoring**: CloudWatch alarms and metrics
- **High Availability**: Multi-AZ database, Redis replication, ALB health checks

## Architecture

```
Internet
   |
   v
Application Load Balancer (Public Subnets)
   |
   ├─> Frontend (Port 5173) ──┐
   └─> Backend API (Port 8000) │
                                v
                    EC2 Instance (Public Subnet)
                    ├── Docker Compose Stack
                    │   ├── Frontend (React)
                    │   ├── Backend (FastAPI)
                    │   ├── Celery Worker
                    │   ├── Celery Beat
                    │   └── Monitoring (Grafana, Prometheus, Loki)
                    │
                    ├─> RDS PostgreSQL (Private Subnet, Multi-AZ)
                    ├─> ElastiCache Redis (Private Subnet, Multi-AZ)
                    └─> S3 Backup Bucket
```

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- EC2 Key Pair created in your target region
- (Optional) Custom domain and SSL certificate

## Quick Start

### Option 1: AWS Console Deployment

1. **Navigate to CloudFormation Console**
   - Open the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation/)
   - Click "Create stack" → "With new resources"

2. **Upload Template**
   - Select "Upload a template file"
   - Choose `marketplace.yaml`
   - Click "Next"

3. **Configure Stack**
   - **Stack name**: `agenthr-production`
   - **Instance Type**: `t3.2xlarge` (minimum for ML workloads)
   - **Key Pair**: Select your SSH key pair
   - **Allowed CIDR**: Enter your IP or `0.0.0.0/0` for public access
   - **Database Password**: Enter a strong password (min 8 characters)
   - **Alert Email**: (Optional) Enter email for CloudWatch alarms
   - Click "Next"

4. **Configure Stack Options**
   - Add tags if desired
   - Click "Next"

5. **Review and Create**
   - Review all settings
   - Check "I acknowledge that AWS CloudFormation might create IAM resources"
   - Click "Create stack"

6. **Wait for Completion**
   - Stack creation takes approximately 15-20 minutes
   - Monitor progress in the "Events" tab
   - Once complete, check the "Outputs" tab for access URLs

### Option 2: AWS CLI Deployment

```bash
# Set your parameters
STACK_NAME="agenthr-production"
KEY_PAIR_NAME="your-key-pair"
DB_PASSWORD="YourStrongPassword123!"
ALERT_EMAIL="alerts@example.com"
ALLOWED_CIDR="0.0.0.0/0"  # Replace with your IP for security

# Deploy the stack
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://marketplace.yaml \
  --parameters \
    ParameterKey=KeyPairName,ParameterValue=$KEY_PAIR_NAME \
    ParameterKey=DBPassword,ParameterValue=$DB_PASSWORD \
    ParameterKey=AllowedCIDR,ParameterValue=$ALLOWED_CIDR \
    ParameterKey=AlertEmail,ParameterValue=$ALERT_EMAIL \
    ParameterKey=InstanceType,ParameterValue=t3.2xlarge \
    ParameterKey=DBInstanceClass,ParameterValue=db.t3.large \
  --capabilities CAPABILITY_IAM

# Monitor stack creation
aws cloudformation wait stack-create-complete --stack-name $STACK_NAME

# Get outputs
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs'
```

## Parameters

### Application Configuration

| Parameter | Description | Default | Allowed Values |
|-----------|-------------|---------|----------------|
| `InstanceType` | EC2 instance type for application | `t3.2xlarge` | t3.xlarge, t3.2xlarge, m5.xlarge, m5.2xlarge, m5.4xlarge, c5.2xlarge, c5.4xlarge |
| `KeyPairName` | SSH key pair name | *Required* | Existing EC2 key pair |
| `AllowedCIDR` | IP range allowed to access the application | `0.0.0.0/0` | Valid CIDR block |

### Database Configuration

| Parameter | Description | Default | Allowed Values |
|-----------|-------------|---------|----------------|
| `DBInstanceClass` | RDS instance class | `db.t3.large` | db.t3.medium, db.t3.large, db.r5.large, etc. |
| `DBAllocatedStorage` | Database storage size (GB) | `100` | 20-1000 |
| `DBUsername` | Database admin username | `agenthr` | Alphanumeric |
| `DBPassword` | Database admin password | *Required* | Min 8 characters |

### Cache Configuration

| Parameter | Description | Default | Allowed Values |
|-----------|-------------|---------|----------------|
| `CacheNodeType` | ElastiCache Redis node type | `cache.t3.medium` | cache.t3.micro, cache.t3.small, cache.r5.large, etc. |

### Monitoring & Backup

| Parameter | Description | Default |
|-----------|-------------|---------|
| `AlertEmail` | Email for CloudWatch alarms | *(Optional)* |
| `BackupRetentionDays` | Backup retention period | `30` |
| `EnableS3Backup` | Enable S3 backup bucket | `true` |

## Accessing Your Deployment

After stack creation completes, retrieve the outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name agenthr-production \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table
```

### Access URLs

- **Application**: `http://<ALB-DNS-Name>`
- **Backend API**: `http://<ALB-DNS-Name>/api`
- **API Documentation**: `http://<ALB-DNS-Name>/docs`
- **Grafana Dashboard**: `http://<Instance-IP>:3001` (Default: admin/admin)

### SSH Access

```bash
ssh -i /path/to/your-key.pem ec2-user@<Instance-Public-IP>
```

## Post-Deployment Configuration

### 1. Access the Application Server

```bash
# SSH into the instance
ssh -i your-key.pem ec2-user@<instance-ip>

# Navigate to application directory
cd /opt/agenthr
```

### 2. Deploy Application Code

The CloudFormation template sets up the infrastructure but requires the application code to be deployed:

```bash
# Clone the repository (update with actual repository URL)
sudo git clone https://github.com/your-org/agenthr.git /opt/agenthr
cd /opt/agenthr

# Copy the generated environment file
sudo cp /opt/agenthr/.env.production .env.production

# Start the application
sudo docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

### 3. Initialize the Database

```bash
# Run database migrations
sudo docker-compose exec backend alembic upgrade head

# (Optional) Create initial admin user
sudo docker-compose exec backend python scripts/create_admin.py
```

### 4. Configure SSL/TLS (Recommended)

#### Option A: Using AWS Certificate Manager (ACM)

1. **Request a Certificate**
   ```bash
   aws acm request-certificate \
     --domain-name yourdomain.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. **Update Load Balancer**
   - Add HTTPS listener on port 443
   - Attach ACM certificate
   - Redirect HTTP to HTTPS

#### Option B: Using Let's Encrypt

```bash
# SSH into the instance
ssh -i your-key.pem ec2-user@<instance-ip>

# Install Certbot
sudo yum install -y certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Configure nginx/application to use certificates
```

### 5. Configure Grafana

1. Access Grafana at `http://<instance-ip>:3001`
2. Login with credentials from Secrets Manager (default: admin/admin)
3. Change default password
4. Configure alert notification channels
5. Import pre-configured dashboards

### 6. Set Up Automated Backups

Backups are automatically configured:

- **Database**: RDS automated backups (30-day retention)
- **Redis**: Daily snapshots (7-day retention)
- **Application**: S3 bucket with lifecycle policies

To manually trigger a backup:

```bash
sudo docker-compose exec backend python scripts/backup.py
```

## Monitoring and Alerts

### CloudWatch Alarms

The stack creates the following alarms (if email is provided):

- **High CPU**: EC2 CPU > 80% for 10 minutes
- **High Memory**: Memory > 80% for 10 minutes
- **Database CPU**: RDS CPU > 80% for 10 minutes
- **Low Storage**: Database free storage < 10GB

### Grafana Dashboards

Pre-configured dashboards monitor:

- Application performance metrics
- Database connections and queries
- Celery task queue status
- Container resource usage
- API response times

### Application Logs

Access logs via CloudWatch Logs or Grafana Loki:

```bash
# View backend logs
sudo docker-compose logs -f backend

# View Celery worker logs
sudo docker-compose logs -f celery_worker
```

## Cost Estimation

Approximate monthly costs (us-east-1 region):

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| EC2 Instance | t3.2xlarge | ~$245 |
| RDS PostgreSQL | db.t3.large, Multi-AZ | ~$240 |
| ElastiCache Redis | cache.t3.medium, 2 nodes | ~$100 |
| Application Load Balancer | - | ~$25 |
| NAT Gateway | - | ~$35 |
| EBS Storage | 100GB | ~$10 |
| S3 Storage | 100GB | ~$2 |
| Data Transfer | 1TB | ~$90 |
| **Total** | | **~$750/month** |

> **Note**: Costs vary based on usage, region, and configuration. Use the [AWS Pricing Calculator](https://calculator.aws/) for accurate estimates.

## Scaling

### Vertical Scaling

Update instance types via CloudFormation:

```bash
aws cloudformation update-stack \
  --stack-name agenthr-production \
  --use-previous-template \
  --parameters \
    ParameterKey=InstanceType,ParameterValue=m5.4xlarge \
    ParameterKey=DBInstanceClass,ParameterValue=db.r5.xlarge
```

### Horizontal Scaling

For high-traffic deployments, consider:

1. **Auto Scaling Group**: Replace single EC2 instance with ASG
2. **ECS/Fargate**: Containerized deployment with auto-scaling
3. **RDS Read Replicas**: Offload read queries
4. **ElastiCache Cluster Mode**: Shard data across multiple nodes

## Backup and Disaster Recovery

### Automated Backups

- **RDS**: Automated daily backups with 30-day retention
- **Redis**: Daily snapshots with 7-day retention
- **S3**: Versioning enabled with lifecycle policies

### Manual Backup

```bash
# Create database snapshot
aws rds create-db-snapshot \
  --db-instance-identifier agenthr-production-postgres \
  --db-snapshot-identifier manual-backup-$(date +%Y%m%d)

# Backup application data to S3
sudo docker-compose exec backend python scripts/backup_to_s3.py
```

### Disaster Recovery

1. **Restore from RDS Snapshot**
   ```bash
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier agenthr-restored \
     --db-snapshot-identifier manual-backup-20260322
   ```

2. **Update Application Configuration**
   ```bash
   # Update DATABASE_URL in Secrets Manager
   aws secretsmanager update-secret \
     --secret-id agenthr-production-secrets \
     --secret-string '{"DATABASE_URL":"new-endpoint"}'
   ```

## Updating the Stack

### Update CloudFormation Template

```bash
aws cloudformation update-stack \
  --stack-name agenthr-production \
  --template-body file://marketplace.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_IAM
```

### Update Application Code

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@<instance-ip>

# Pull latest changes
cd /opt/agenthr
sudo git pull origin main

# Rebuild and restart containers
sudo docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d --build
```

## Troubleshooting

### Stack Creation Fails

1. **Check CloudFormation Events**
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name agenthr-production \
     --max-items 10
   ```

2. **Common Issues**
   - Invalid key pair name
   - Insufficient EC2 limits
   - Invalid CIDR block
   - Database password requirements not met

### Application Not Accessible

1. **Verify Security Groups**
   ```bash
   aws ec2 describe-security-groups \
     --filters "Name=group-name,Values=agenthr-production-alb-sg"
   ```

2. **Check Target Health**
   ```bash
   aws elbv2 describe-target-health \
     --target-group-arn <target-group-arn>
   ```

3. **Check Docker Containers**
   ```bash
   sudo docker-compose ps
   sudo docker-compose logs backend
   ```

### Database Connection Issues

1. **Verify Security Group Rules**
   - Ensure AppSecurityGroup can access DBSecurityGroup on port 5432

2. **Check Database Status**
   ```bash
   aws rds describe-db-instances \
     --db-instance-identifier agenthr-production-postgres
   ```

3. **Test Connection**
   ```bash
   sudo docker-compose exec backend python -c "from database import engine; print(engine.execute('SELECT 1').fetchone())"
   ```

## Security Best Practices

1. **Restrict Access**
   - Update `AllowedCIDR` to your specific IP range
   - Use VPN for administrative access

2. **Enable SSL/TLS**
   - Configure HTTPS listener with ACM certificate
   - Enforce HTTPS redirects

3. **Rotate Credentials**
   ```bash
   # Update database password
   aws rds modify-db-instance \
     --db-instance-identifier agenthr-production-postgres \
     --master-user-password "NewSecurePassword123!"

   # Update Secrets Manager
   aws secretsmanager update-secret \
     --secret-id agenthr-production-secrets \
     --secret-string '{...}'
   ```

4. **Enable MFA**
   - Enable MFA for AWS console access
   - Use IAM roles instead of access keys

5. **Regular Updates**
   - Keep Docker images updated
   - Apply security patches to EC2 instances
   - Update RDS engine version during maintenance windows

## Maintenance

### Scheduled Maintenance Windows

- **RDS**: Sundays 04:00-05:00 UTC
- **ElastiCache**: Sundays 05:00-06:00 UTC
- **Application Updates**: Deploy during low-traffic periods

### Health Checks

Monitor health endpoints:

```bash
# Backend health
curl http://<alb-dns>/health

# Frontend health
curl http://<alb-dns>/

# Database health
aws rds describe-db-instances \
  --db-instance-identifier agenthr-production-postgres \
  --query 'DBInstances[0].DBInstanceStatus'
```

## Cleanup

To delete the entire stack and all resources:

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name agenthr-production

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name agenthr-production
```

**Warning**: This will permanently delete all data, including databases and backups. Create snapshots before deletion if you need to preserve data.

## Support

For issues and questions:

- **GitHub Issues**: https://github.com/your-org/agenthr/issues
- **Documentation**: https://docs.agenthr.com
- **AWS Support**: Use AWS Support Center for infrastructure issues

## License

This CloudFormation template is provided under the same license as the AgentHR application.
