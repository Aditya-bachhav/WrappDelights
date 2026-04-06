# Data Persistence Configuration ✅

This document verifies that your Wrapp Delights catalog will NOT lose data on deployment.

## Setup Status: ✅ CONFIGURED FOR PERSISTENT DATA

### How It Works

**Production (Render):**
- Uses **PostgreSQL database** (wrapp-delights-db) - persists across deployments
- Environment variable `DATABASE_URL` is automatically populated by Render from the database service
- Database is separate from the application, survives redeployment

**Local Development:**
- Falls back to SQLite (db.sqlite3) for convenience
- No data loss when running locally

### Critical Safety Checks ✅

**1. Build Script (build.sh):**
- ✅ Runs collectstatic only
- ✅ NO `flush` or destructive commands
- ✅ Migrations moved to startCommand (run after database is ready)

**2. Deployment Script (render.yaml startCommand):**
- ✅ Migrations run ONLY after persistent database is online
- ✅ Command: `python manage.py migrate --no-input` (doesn't destroy data)
- ✅ Superuser is created/updated (doesn't destroy existing users or products)

**3. Django Settings (settings.py):**
- ✅ Uses `dj_database_url` to read DATABASE_URL from environment
- ✅ SSL required for secure database connection
- ✅ SAFETY ALERT: If Render is detected but DATABASE_URL is missing, app will NOT START
  - This prevents accidental data loss from using SQLite on Render

### Verify Data Persistence on Render

**Check 1: Verify PostgreSQL is configured**
```
Go to Render Dashboard → Your Service (wrapp-delights)
→ Environment → Look for DATABASE_URL variable
Expected: Should show a value like "postgresql://user:pass@host:port/dbname"
```

**Check 2: After deployment, verify database is being used**
```
Django Admin → Login with Admin / D^L!G#t$0@dm/7404
→ Add a test product
→ Trigger a redeployment (git push)
→ Check if product is still there
Expected: Product should persist ✅
```

**Check 3: Monitor for database errors**
```
Render Dashboard → Logs
Search for: "DATABASE_URL", "postgresql", "ERROR"
Expected: No database connection errors
```

### ⚠️ DANGER ZONE - Commands That DESTROY Data

**NEVER run these in production:**
```bash
python manage.py flush                  # ❌ Deletes all data
python manage.py sqlsequencereset       # ❌ Resets sequences
```

**Safe migrations:**
```bash
python manage.py migrate                # ✅ Applies pending migrations safely
python manage.py makemigrations         # ✅ Creates migration files
```

### Data Backup Recommendation

Since you have important product data, consider:

1. **Render PostgreSQL Backups** (Free tier: automatic backups)
   - Render keeps 7-day automatic backups
   - Manual backup: `pg_dump` from Render PostgreSQL service

2. **CSV Export** (Built-in)
   - Periodically export products to CSV
   - Keep in your repository or cloud storage

## Deployment Flow (Safe Process)

```
git push
        ↓
Render builds (installs pip packages, collects static files)
        ↓
Render starts service (postgres database is online)
        ↓
Migrations run (applies schema changes WITHOUT deleting data)
        ↓
Superuser is created/updated (doesn't affect existing data)
        ↓
Gunicorn server starts
        ↓
Your products, orders, users are safe ✅
```

## Troubleshooting

**Problem: "ValueError: DATABASE_URL is not set"**
- This is intentional! It means Render detected but no DATABASE_URL
- Solution: Go to Render Dashboard → Environment → Verify DATABASE_URL is linked to wrapp-delights-db

**Problem: Products disappear after deployment**
- Check Logs for "DATABASE_URL" errors
- Verify DATABASE_URL environment variable is configured
- Contact Render support if PostgreSQL service is down

**Problem: Want to reset database (intentionally)**
- Only run this if you know you want to delete all data:
  ```bash
  python manage.py flush --no-input
  python manage.py ensure_superuser
  ```
- This should ONLY be done in emergencies, not during normal deployments

---

**Last Updated:** April 7, 2026
**Next Step:** Verify your render.yaml has the `databases:` section with PostgreSQL configured
