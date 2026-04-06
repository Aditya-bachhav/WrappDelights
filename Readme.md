# WrappDelights

Django-based gifting catalog with custom hamper builder and admin dashboard.

## 1. Project Structure (Actual)

```text
wrapp_delights/
|-- build.sh
|-- render.yaml
|-- requirements.txt
|-- Readme.md
|-- delights_backend/
|   |-- __init__.py
|   |-- core/
|   |   |-- manage.py
|   |   |-- db.sqlite3
|   |   |-- core/
|   |   |   |-- __init__.py
|   |   |   |-- settings.py
|   |   |   |-- urls.py
|   |   |   |-- wsgi.py
|   |   |   `-- asgi.py
|   |   |-- store/
|   |   |   |-- __init__.py
|   |   |   |-- admin.py
|   |   |   |-- apps.py
|   |   |   |-- context_processors.py
|   |   |   |-- models.py
|   |   |   |-- views.py
|   |   |   |-- tests.py
|   |   |   |-- migrations/
|   |   |   |   |-- 0001_initial.py
|   |   |   |   |-- ...
|   |   |   |   `-- 0010_hamper_base_price.py
|   |   |   |-- management/
|   |   |   |   `-- commands/
|   |   |   |      |-- ensure_superuser.py
|   |   |   |      |-- import_products.py
|   |   |   |      |-- seed_catalog.py
|   |   |   |      `-- assign_categories.py
|   |   |   |-- templates/
|   |   |   |   |-- base.html
|   |   |   |   |-- home.html
|   |   |   |   |-- products.html
|   |   |   |   |-- product_detail.html
|   |   |   |   |-- corporate.html
|   |   |   |   |-- corporate_success.html
|   |   |   |   |-- custom_hamper_step.html
|   |   |   |   |-- custom_hamper_review.html
|   |   |   |   |-- login.html
|   |   |   |   |-- search.html
|   |   |   |   |-- dashboard/
|   |   |   |   `-- partials/
|   |   |   |-- static/
|   |   |   |-- media/
|   |   |   `-- staticfiles/
|   |   `-- assign_categories.py
```

Notes:
- The correct `manage.py` path is: `delights_backend/core/manage.py`
- This is why `python manage.py ...` from repo root fails on Render.

## 2. Local Run Commands

From repo root (`wrapp_delights`):

```bash
python delights_backend/core/manage.py migrate
python delights_backend/core/manage.py runserver
```

Optional admin bootstrap locally:

```bash
python delights_backend/core/manage.py ensure_superuser
```

## 3. Render Commands (Important)

Build Command:

```bash
bash build.sh
```

Start Command (recommended):

```bash
cd delights_backend/core && python manage.py migrate --noinput && python manage.py ensure_superuser && exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

Why this is correct:
- `cd delights_backend/core` puts shell in the folder where `manage.py` exists.
- `migrate` and `ensure_superuser` run before server boot.
- `exec gunicorn ... --bind 0.0.0.0:$PORT` is Render-safe and avoids startup hangs.

## 4. Render Environment Variables

Required for admin bootstrap:

```text
ADMIN_BOOTSTRAP_USERNAME=Admin
ADMIN_BOOTSTRAP_PASSWORD=<your-password>
ADMIN_BOOTSTRAP_EMAIL=<optional-email>
ADMIN_PANEL_PATH=<your-secret-admin-path>/
```

Other key vars used in this project:

```text
DATABASE_URL=<render-postgres-connection-string>
SECRET_KEY=<render-secret>
DEBUG=False
ALLOWED_HOSTS=.onrender.com
MEDIA_ROOT=/var/data/media
```

## 5. Admin Access Model

- Django admin is mounted at secret path from `ADMIN_PANEL_PATH`.
- Custom dashboard remains at `/dashboard/`.
- Admin/dashboard access is restricted to superusers.

## 6. Common Deployment Pitfalls

1. Wrong start command path:
- Wrong: `python manage.py ...`
- Correct: `cd delights_backend/core && python manage.py ...`

2. Static admin CSS missing (404):
- Ensure Build Command is exactly `bash build.sh`.

3. Admin login fails:
- Check deploy logs for `Superuser 'Admin' created.` or `updated.`
- If missing, `ensure_superuser` did not run or env vars are missing.

4. Hidden admin URL confusion:
- If `ADMIN_PANEL_PATH=wrappdelightstoadminx/`, URL is:
	`https://<domain>/wrappdelightstoadminx/`

## 7. Useful File References

- Django settings: `delights_backend/core/core/settings.py`
- URL routing: `delights_backend/core/core/urls.py`
- Main app views: `delights_backend/core/store/views.py`
- Bootstrap admin command: `delights_backend/core/store/management/commands/ensure_superuser.py`
- Deploy config: `render.yaml`
- Build script: `build.sh`