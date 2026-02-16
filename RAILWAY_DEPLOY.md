# Quick Deploy to Railway

## One-Click Setup

1. **Fork Repository** (if not already done)
   - Go to: <https://github.com/vithaluntold/RAi-Platform>
   - Click "Fork"

2. **Create Railway Account**
   - Visit: <https://railway.app>
   - Sign up with GitHub

3. **Deploy Backend**
   
   ```bash
   # In Railway dashboard:
   # 1. New Project → Deploy from GitHub
   # 2. Select: vithaluntold/RAi-Platform
   # 3. Add PostgreSQL database
   # 4. Create service from repo
   # 5. Set root directory: backend
   # 6. Add environment variables (see below)
   ```

4. **Deploy Frontend**
   
   ```bash
   # In same Railway project:
   # 1. New service from repo
   # 2. Set root directory: frontend  
   # 3. Add environment variable:
   #    NEXT_PUBLIC_API_URL=<your-backend-url>
   ```

5. **Initialize Database**
   
   ```bash
   # In backend service terminal:
   alembic upgrade head
   python seed_db.py
   ```

## Required Environment Variables

### Backend Service

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=<generate-with-command-below>
JWT_SECRET_KEY=<generate-with-command-below>
AZURE_OPENAI_ENDPOINTS=["https://your-openai.openai.azure.com"]
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com
AZURE_DOC_INTELLIGENCE_KEY=your-key
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX_NAME=compliance-docs
CORS_ORIGINS=["${{RAILWAY_PUBLIC_DOMAIN}}"]
```

### Frontend Service

```env
NEXT_PUBLIC_API_URL=https://${{backend.RAILWAY_PUBLIC_DOMAIN}}/api/v1
```

## Generate Secrets

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run this twice - once for `SECRET_KEY`, once for `JWT_SECRET_KEY`.

## Post-Deploy Checklist

- [ ] Backend health check: `https://your-backend.railway.app/health`
- [ ] Frontend loads: `https://your-frontend.railway.app`
- [ ] Database seeded with users
- [ ] Login with `admin@rai-platform.com` / `Admin@123456`
- [ ] Change default passwords
- [ ] Test compliance analysis workflow
- [ ] Verify agent registry shows compliance agent

## Estimated Deploy Time

- Database: ~2 minutes
- Backend: ~5 minutes (includes migrations)
- Frontend: ~3 minutes
- **Total: ~10 minutes**

## Cost Estimate (Railway)

- Hobby Plan: $5/month (500 hours execution)
- PostgreSQL: Included
- **Total: $5-10/month** (plus Azure API costs)

Azure costs depend on usage:

- OpenAI GPT-4: ~$0.03/1K tokens
- Document Intelligence: ~$10/1K pages
- AI Search: ~$75/month (Basic tier)

**Typical monthly cost: $100-200** for moderate usage.

## Need Help?

See full guide: [DEPLOYMENT.md](DEPLOYMENT.md)
