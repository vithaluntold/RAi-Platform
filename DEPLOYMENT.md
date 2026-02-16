# Railway Deployment Guide

## Prerequisites

- Railway account ([railway.app](https://railway.app))
- GitHub repository connected
- PostgreSQL database provisioned on Railway

## Deployment Steps

### 1. Database Setup

1. Create a new PostgreSQL database in Railway
2. Note the connection string from the database service

### 2. Backend Deployment

1. Create a new service in Railway
2. Connect to GitHub repository: `vithaluntold/RAi-Platform`
3. Set root directory: `/backend`
4. Railway will auto-detect the Dockerfile

**Environment Variables (Backend):**

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# API
API_V1_STR=/api/v1
PROJECT_NAME=RAi-Platform
SECRET_KEY=<generate-secure-secret-key>

# JWT
JWT_SECRET_KEY=<generate-secure-jwt-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Azure OpenAI
AZURE_OPENAI_ENDPOINTS=["https://your-openai.openai.azure.com"]
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure Document Intelligence
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com
AZURE_DOC_INTELLIGENCE_KEY=your-key

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX_NAME=compliance-docs

# Keycloak (Optional)
KEYCLOAK_SERVER_URL=https://your-keycloak.com
KEYCLOAK_REALM=rai-platform
KEYCLOAK_CLIENT_ID=rai-web
KEYCLOAK_CLIENT_SECRET=your-secret
KEYCLOAK_AD_ENABLED=false

# CORS
CORS_ORIGINS=["https://your-frontend.railway.app"]
```

**Generate secure keys:**
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Frontend Deployment

1. Create another service in Railway
2. Connect to same GitHub repository
3. Set root directory: `/frontend`
4. Railway will auto-detect the Dockerfile

**Environment Variables (Frontend):**

```bash
# API
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1

# NextJS
NODE_ENV=production
```

### 4. Post-Deployment

1. **Run Database Migrations** (Backend service terminal):
   ```bash
   alembic upgrade head
   ```

2. **Seed Database** (Backend service terminal):
   ```bash
   python seed_db.py
   ```

3. **Verify Health** - Visit:
   - Backend: `https://your-backend.railway.app/health`
   - Frontend: `https://your-frontend.railway.app`

### 5. Default Credentials (After Seeding)

```
Admin:
Email: admin@rai-platform.com
Password: Admin@123456

Manager:
Email: manager@rai-platform.com
Password: Manager@123456
```

**⚠️ IMPORTANT: Change these passwords in production!**

## Railway Configuration Files

- `backend/Dockerfile` - Backend container configuration
- `frontend/Dockerfile` - Frontend container configuration  
- `railway.json` - Railway deployment settings
- `.dockerignore` - Files excluded from Docker builds

## Troubleshooting

### Backend won't start
1. Check DATABASE_URL is correct
2. Verify all Azure environment variables are set
3. Check logs: Railway dashboard → Service → Logs

### Frontend can't connect to backend
1. Verify NEXT_PUBLIC_API_URL points to backend service
2. Check CORS_ORIGINS in backend includes frontend URL
3. Ensure backend service is running

### Database migration errors
1. Run `alembic current` to check migration state
2. If needed, reset: `alembic downgrade base` then `alembic upgrade head`
3. Check PostgreSQL connection and permissions

### Compliance analysis fails
1. Verify all Azure credentials are valid
2. Check Azure OpenAI quota and deployment
3. Verify Document Intelligence service is active
4. Check Azure Search index exists and is accessible

## Monitoring

- **Backend logs**: Railway dashboard → Backend service → Logs
- **Frontend logs**: Railway dashboard → Frontend service → Logs
- **Database**: Railway dashboard → PostgreSQL service → Metrics
- **Health endpoint**: `GET /health` returns 200 OK when healthy

## Scaling

Railway auto-scales based on load. For manual scaling:
1. Go to service settings
2. Adjust replicas under "Deploy" settings
3. Configure resource limits if needed

## CI/CD

Railway automatically deploys on push to `main` branch:
1. Push to GitHub → Triggers Railway build
2. Railway builds Docker images
3. Runs health checks
4. Deploys if successful
5. Falls back to previous version if failed

## Security Best Practices

1. ✅ Use strong SECRET_KEY and JWT_SECRET_KEY
2. ✅ Enable HTTPS (Railway provides by default)
3. ✅ Restrict CORS_ORIGINS to your frontend domain only
4. ✅ Change default seed passwords immediately
5. ✅ Rotate Azure API keys regularly
6. ✅ Enable Railway's built-in DDoS protection
7. ✅ Monitor logs for suspicious activity
8. ✅ Keep dependencies updated

## Cost Optimization

- Use Railway's starter plan for development
- Optimize Docker images (already multi-stage)
- Use caching for compliance analysis results
- Monitor Azure API usage (main cost driver)
- Set up budget alerts in Azure portal

## Support

- Railway docs: https://docs.railway.app
- GitHub issues: https://github.com/vithaluntold/RAi-Platform/issues
- Backend API docs: `https://your-backend.railway.app/docs`
