# Deployment Guide for Wingman Flight Logbook

This guide will help you deploy your Django flight logbook application to a live website.

## Quick Deploy Options (Recommended)

### Option 1: Railway (Easiest - $5-20/month)

1. **Sign up** at [railway.app](https://railway.app)
2. **Connect your GitHub** repository
3. **Create a new project** and select "Deploy from GitHub repo"
4. **Select your repository** and branch
5. **Add environment variables**:
   - `SECRET_KEY`: Generate a new secret key
   - `ALLOWED_HOSTS`: Your railway domain (e.g., `your-app.railway.app`)
   - `DATABASE_URL`: Railway will provide this automatically
6. **Deploy** - Railway will automatically detect Django and deploy

### Option 2: Render (Great Alternative - $7/month)

1. **Sign up** at [render.com](https://render.com)
2. **Create a new Web Service**
3. **Connect your GitHub** repository
4. **Configure the service**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wingman.wsgi:application`
   - **Environment**: Python 3
5. **Add environment variables**:
   - `SECRET_KEY`: Generate a new secret key
   - `ALLOWED_HOSTS`: Your render domain
   - `DATABASE_URL`: Create a PostgreSQL database in Render
6. **Deploy**

### Option 3: DigitalOcean App Platform ($5-12/month)

1. **Sign up** at [digitalocean.com](https://digitalocean.com)
2. **Create a new App**
3. **Connect your GitHub** repository
4. **Configure**:
   - **Source**: GitHub
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `gunicorn wingman.wsgi:application`
5. **Add environment variables** (same as above)
6. **Deploy**

## Pre-Deployment Checklist

### 1. Generate a Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Run Migrations Locally

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Collect Static Files

```bash
python manage.py collectstatic
```

### 4. Test Production Settings

```bash
python manage.py runserver --settings=wingman.production
```

## Environment Variables

Set these in your deployment platform:

- `SECRET_KEY`: Your Django secret key
- `ALLOWED_HOSTS`: Your domain (comma-separated if multiple)
- `DATABASE_URL`: Database connection string (provided by platform)

## Custom Domain Setup

After deployment, you can add a custom domain:

1. **Purchase a domain** (Namecheap, GoDaddy, etc.)
2. **Point DNS** to your deployment platform
3. **Add domain** to your platform settings
4. **Update ALLOWED_HOSTS** to include your custom domain

## Cost Comparison

| Platform     | Monthly Cost | Database | SSL | Custom Domain |
| ------------ | ------------ | -------- | --- | ------------- |
| Railway      | $5-20        | ✅       | ✅  | ✅            |
| Render       | $7           | ✅       | ✅  | ✅            |
| DigitalOcean | $5-12        | ✅       | ✅  | ✅            |
| Heroku       | $7           | ✅       | ✅  | ✅            |

## Troubleshooting

### Common Issues:

1. **Static files not loading**: Ensure `collectstatic` was run
2. **Database errors**: Check `DATABASE_URL` environment variable
3. **500 errors**: Check logs in your deployment platform
4. **Media uploads**: Consider using cloud storage (AWS S3, Cloudinary)

### Getting Help:

- Check your platform's logs
- Review Django deployment checklist: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- Contact platform support

## Next Steps After Deployment

1. **Set up monitoring** (optional)
2. **Configure backups** for your database
3. **Set up CI/CD** for automatic deployments
4. **Add analytics** (Google Analytics, etc.)
5. **Set up email** for password resets (if needed)
