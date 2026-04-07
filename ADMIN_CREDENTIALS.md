# Admin Credentials & Bootstrap

## Current Admin Account

**Hardcoded credentials for the deployed admin account:**

- **Username**: `admin` (lowercase)
- **Password**: `D^L!G#t$0@dm/7404` (includes literal `$` and `0`)
- **Email**: `admin@example.com`

### What This Means

These credentials are hardcoded in:
- `delights_backend/core/store/management/commands/ensure_admin_user.py`

And they are enforced at every application startup via the `ensure_admin_user` management command.

## Bootstrap Process

### On Render (Production)

The startup sequence in `render.yaml`:

1. Create media directory
2. Run database migrations
3. **Run `ensure_admin_user` command** — enforces the fixed admin account
4. Start Gunicorn

**Result**: Admin account is created/updated with the hardcoded credentials above.

### Locally (Development)

Same flow when you run:

```bash
cd delights_backend/core
python manage.py migrate
python manage.py ensure_admin_user
python manage.py runserver
```

Or if migrations/bootstrap fail to run:

```bash
python manage.py ensure_admin_user --verbosity 2
```

## Login URLs

### Custom Dashboard (Admin Interface)

- **URL**: `http://localhost:8000/login/?next=/dashboard/` (local)
- **URL**: `https://wrappdelights.onrender.com/login/?next=/dashboard/` (production)
- **Username**: `admin` or `Admin` (case-insensitive)
- **Password**: `D^L!G#t$0@dm/7404`

The login form accepts either case for the username because `CaseInsensitiveAuthenticationForm` is used.

### Django Admin (if needed)

- **URL**: `http://localhost:8000/control-room-admin/` (local, default)
- **URL**: `https://wrappdelights.onrender.com/control-room-admin/` (production, default)
- **Path can be customized** via env var: `ADMIN_PANEL_PATH=your-secret-path/`

Same credentials as above.

## No Environment Variables Required

The admin account **does not** depend on `ADMIN_BOOTSTRAP_*` environment variables.

It uses hardcoded defaults only. Environment variables are not set in `render.yaml`, and the code does not listen for them.

If you need to change credentials, you must:

1. Update constants in `delights_backend/core/store/management/commands/ensure_admin_user.py`
2. Commit and push
3. Redeploy (Render will run the updated command at startup)

Or manually in the Django shell:

```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> U = get_user_model()
>>> u = U.objects.get(username='admin')
>>> u.set_password('new-password-here')
>>> u.save()
```

## Summary

- **Single source of truth**: `ensure_admin_user.py`
- **Enforced at startup**: Every boot, the command ensures the hardcoded admin exists
- **No env var coupling**: You don't need environment variables to log in
- **Case-insensitive login**: Username matching is flexible on the login form
- **Password is literal**: The `$` character is part of the password, not a shell variable

If login fails, the most common reasons:

1. **Wrong password** — Double-check the literal string above, character for character
2. **Admin account not created** — Run `python manage.py ensure_admin_user` manually
3. **Stale session/cache** — Open a fresh incognito tab and try again
