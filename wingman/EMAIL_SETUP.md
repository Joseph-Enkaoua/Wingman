# Email Setup with Resend

This guide explains how to configure and use Resend for sending emails in your Wingman Flight Logbook application.

## Prerequisites

1. **Resend Account**: Sign up at [resend.com](https://resend.com)
2. **Domain Verification**: Add and verify your domain in the Resend dashboard
3. **API Key**: Generate an API key from your Resend dashboard

## Environment Variables

Add these environment variables to your `.env` file:

```bash
# Resend Configuration
RESEND_API_KEY=re_your_api_key_here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## Configuration

### 1. Django Settings

The email configuration is already set up in `wingman/settings.py`:

```python
# Email Configuration with Resend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For development
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # For production with Resend

# Resend Configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Email settings for production (when using Resend SMTP)
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = RESEND_API_KEY
```

### 2. Email Utility Functions

The `logbook/email_utils.py` file provides utility functions for sending emails:

- `send_email()` - Main function that chooses between Resend API or Django backend
- `send_email_via_resend()` - Send email using Resend API
- `send_email_via_django()` - Send email using Django's email backend
- `send_password_reset_email()` - Send password reset emails
- `send_welcome_email()` - Send welcome emails to new users

## Usage Examples

### 1. Basic Email Sending

```python
from logbook.email_utils import send_email

# Send a simple email
success = send_email(
    to_email="user@example.com",
    subject="Welcome to Wingman",
    html_content="<h1>Welcome!</h1><p>Thank you for joining.</p>",
    text_content="Welcome! Thank you for joining."
)
```

### 2. Password Reset Email

```python
from logbook.email_utils import send_password_reset_email

# Send password reset email
success = send_password_reset_email(user, reset_url)
```

### 3. Welcome Email

```python
from logbook.email_utils import send_welcome_email

# Send welcome email to new user
success = send_welcome_email(user)
```

### 4. In Your Views

```python
from logbook.email_utils import send_email

def my_view(request):
    # Your view logic here

    # Send email
    success = send_email(
        to_email=user.email,
        subject="Important Update",
        html_content="<p>Your account has been updated.</p>"
    )

    if success:
        messages.success(request, "Email sent successfully!")
    else:
        messages.error(request, "Failed to send email.")
```

## Testing

### 1. Using the Test View (Development Only)

Visit `/test-email/` in your browser when `DEBUG=True` to test email functionality.

### 2. Using Management Command

```bash
# Send a test email
python manage.py test_email --email user@example.com --type test

# Send a welcome email
python manage.py test_email --email user@example.com --type welcome

# Send a password reset email
python manage.py test_email --email user@example.com --type password-reset
```

### 3. Using Django Shell

```python
python manage.py shell

from logbook.email_utils import send_email

# Test basic email
send_email(
    to_email="your-email@example.com",
    subject="Test Email",
    html_content="<p>This is a test email.</p>"
)
```

## Production Setup

### 1. Update Settings

For production, update your settings to use Resend SMTP:

```python
# In production.py or settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```

### 2. Environment Variables

Make sure these are set in your production environment:

```bash
RESEND_API_KEY=re_your_production_api_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 3. Domain Configuration

1. Add your domain in the Resend dashboard
2. Verify your domain by adding DNS records
3. Use your verified domain in the `DEFAULT_FROM_EMAIL` setting

## Email Templates

### 1. Password Reset Template

The password reset email uses the template at `templates/logbook/password_reset_email.html`.

### 2. Custom Templates

You can create custom email templates and use them with `render_to_string()`:

```python
from django.template.loader import render_to_string

html_content = render_to_string('my_email_template.html', {
    'user': user,
    'custom_data': 'value'
})

send_email(
    to_email=user.email,
    subject="Custom Email",
    html_content=html_content
)
```

## Error Handling

The email utility functions include comprehensive error handling:

- Logs all email sending attempts
- Returns `True`/`False` for success/failure
- Gracefully handles API errors
- Falls back to Django email backend if Resend fails

## Monitoring

Check your application logs for email-related messages:

```bash
# View logs
tail -f your_log_file.log | grep -i email
```

## Troubleshooting

### Common Issues

1. **API Key Not Set**: Make sure `RESEND_API_KEY` is in your environment variables
2. **Domain Not Verified**: Verify your domain in the Resend dashboard
3. **Rate Limits**: Resend has rate limits; check your usage in the dashboard
4. **Invalid Email**: Ensure email addresses are valid

### Debug Mode

In development, emails are logged to the console by default. Check your terminal output for email content.

## Security Notes

1. Never commit your API key to version control
2. Use environment variables for sensitive configuration
3. Validate email addresses before sending
4. Implement rate limiting for email sending endpoints
5. Use HTTPS in production

## Support

- [Resend Documentation](https://resend.com/docs)
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- Check application logs for detailed error messages
