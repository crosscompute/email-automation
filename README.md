# Email Automation

For Gmail, use an application-specific password.

```
export ATTACHMENTS_FOLDER=batches/example/input
export SMTP_URL=smtp.gmail.com
export SMTP_PORT=465
export SMTP_USERNAME=YOUR-USERNAME@gmail.com
export SMTP_PASSWORD=YOUR-APPLICATION-SPECIFIC-PASSWORD

# Test script
python run.py batches/example/input/ batches/example/output

# Start server
crosscompute
```

Thanks to https://realpython.com/python-send-email for updated notes on how to send email with Python 3.
