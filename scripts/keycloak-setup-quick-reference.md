# Keycloak Setup Quick Reference

## Fast Path: Automated Setup

```bash
# 1. Start Keycloak
bash scripts/start-keycloak.sh

# 2. Setup realm, clients, roles
bash scripts/setup-keycloak-realm.sh

# 3. Verify configuration
bash scripts/verify-subtask-1-4.sh
```

## What Gets Created

| Resource | Name/ID | Type | Details |
|----------|---------|------|---------|
| Realm | `agenthr` | - | Enabled, registration allowed |
| Frontend Client | `agenthr-frontend` | Public | Redirect: http://localhost:5173/* |
| Backend Client | `agenthr-backend` | Confidential | Redirect: http://localhost:8000/* |
| Role | `Admin` | Realm | Full system access |
| Role | `Recruiter` | Realm | Hiring workflow access |
| Role | `Viewer` | Realm | Read-only access |
| User | `admin` | - | Password: admin123, Role: Admin |

## Keycloak URLs

- **Admin Console**: http://localhost:8080/admin
- **Realm Console**: http://localhost:8080/admin/master/console/#/realms/agenthr
- **Account Console**: http://localhost:8080/realms/agenthr/account
- **Health Endpoint**: http://localhost:8080/health/ready
- **OpenID Config**: http://localhost:8080/realms/agenthr/.well-known/openid-configuration

## Required Environment Variables

```bash
# Backend (.env)
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=agenthr
KEYCLOAK_CLIENT_ID=agenthr-backend
KEYCLOAK_CLIENT_SECRET=<from setup script output>

# Frontend (.env)
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=agenthr
VITE_KEYCLOAK_CLIENT_ID=agenthr-frontend
```

## Manual Setup Steps (GUI)

If automated script doesn't work, use Admin Console:

1. **Create Realm**: Admin Console → Create Realm → `agenthr`
2. **Create Frontend Client**: Clients → Create → `agenthr-frontend` (Public)
3. **Create Backend Client**: Clients → Create → `agenthr-backend` (Confidential)
4. **Create Roles**: Realm Roles → Create → Admin, Recruiter, Viewer
5. **Create Admin User**: Users → Add → `admin` (password: `admin123`)

## Verification Checklist

- [ ] Realm `agenthr` exists and is enabled
- [ ] Client `agenthr-frontend` exists (Public)
- [ ] Client `agenthr-backend` exists (Confidential)
- [ ] Roles Admin, Recruiter, Viewer exist
- [ ] Default admin user can login
- [ ] Backend client secret saved to `.env`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Keycloak not available | Run `bash scripts/start-keycloak.sh` |
| Realm already exists | Setup script will ask to recreate |
| Can't get client secret | Admin Console → Clients → agenthr-backend → Credentials |
| User can't login | Check user is enabled, email verified, password set |

## Default Credentials

| Purpose | Username | Password |
|---------|----------|----------|
| Admin Console | admin | admin |
| Realm User | admin | admin123 |

⚠️ **Change these in production!**
