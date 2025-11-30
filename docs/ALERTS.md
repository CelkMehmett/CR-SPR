
# Alerts & Notification Setup

This document explains how to configure the Alerts system in CRISPR-FinAI and how to enable Email and Telegram channels.

Files involved

- `core/alerts.py` - alert data model and manager
- `core/api_server.py` - endpoints to register, list, evaluate and remove alerts

Environment variables

To enable outgoing Email notifications, set the following environment variables (example in `.env`):

```env
ALERT_SMTP_HOST=smtp.example.com
ALERT_SMTP_PORT=587
ALERT_SMTP_USER=bot@example.com
ALERT_SMTP_PASS=supersecret
ALERT_EMAIL_TO=ops-team@example.com
```

Notes:

- The current implementation uses a simple `smtplib.SMTP` client with STARTTLS. If your provider requires different settings (SSL port 465 or OAuth), update `core/alerts.py::_send_email` accordingly.

To enable Telegram notifications, set:

```env
ALERT_TELEGRAM_BOT=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ALERT_TELEGRAM_CHAT=987654321
```

Usage examples

- Create an alert via API:

```http
POST /api/alerts
Authorization: Bearer <token>
{
  "name": "low_sharpe",
  "condition": "metrics.get(\"sharpe\", 0) < 0.8",
  "channels": ["log", "email"]
}
```

- Evaluate alerts (usually used by monitoring scripts):

```http
POST /api/alerts/evaluate
Authorization: Bearer <token>
{
  "metrics": {"sharpe": 0.6, "drawdown": -5.2}
}
```

Security and safety

- Conditions are evaluated using a restricted AST-based evaluator. Allowed constructs include boolean operators, comparisons, arithmetic, `metrics[...]`, and `metrics.get(...)`. Avoid complex expressions that rely on external libraries.
- Email and Telegram channels are only used if environment variables are present. In development, alerts default to printing to the service logs.

Testing alerts locally

1. Set environment variables in your shell or use a `.env` file.
1. Run the API server:

```bash
uvicorn core.api_server:app --reload
```

1. Use `curl` or Postman to create and evaluate alerts.

Troubleshooting

- If emails are not sent, enable debug prints in `_send_email` and check connectivity to your SMTP server.
- If Telegram messages are not sent, verify bot token and chat id by testing with a simple curl to Telegram's sendMessage API.

