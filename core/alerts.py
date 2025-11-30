"""
Alert & Notification system (lightweight)

Provides:
- AlertManager: register/list/remove alerts
- Simple rule engine: evaluate a metric dict against conditions
- Safe send stubs for email and Telegram (disabled unless env vars provided)
"""
from typing import Any, Dict, List, Optional
import os
import smtplib
import json
import ast
from ast import AST


class Alert:
    def __init__(self, name: str, condition: str, channels: Optional[List[str]] = None, metadata: Optional[Dict] = None):
        self.name = name
        self.condition = condition  # python expression, e.g. "metrics['sharpe'] < 0.5"
        self.channels = channels or ['log']
        self.metadata = metadata or {}

    def to_dict(self):
        return {'name': self.name, 'condition': self.condition, 'channels': self.channels, 'metadata': self.metadata}


class AlertManager:
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}

    def register(self, alert: Alert):
        self.alerts[alert.name] = alert

    def list(self):
        return [a.to_dict() for a in self.alerts.values()]

    def remove(self, name: str):
        if name in self.alerts:
            del self.alerts[name]

    def evaluate(self, metrics: Dict[str, Any]):
        hits = []
        for a in self.alerts.values():
            try:
                # Use a safe AST-based evaluator to avoid arbitrary code execution
                if _safe_eval_condition(a.condition, metrics):
                    hits.append(a.name)
                    self._notify(a, metrics)
            except Exception:
                # If evaluation fails (syntax, unsafe node, etc.) treat as non-hit but log
                print(f"[ALERT] Failed to evaluate condition for '{a.name}': {a.condition}")
                continue
        return hits

    def _notify(self, alert: Alert, metrics: Dict[str, Any]):
        payload = {'alert': alert.to_dict(), 'metrics': metrics}
        for ch in alert.channels:
            if ch == 'log':
                print(f"[ALERT:{alert.name}] {json.dumps(payload)}")
            elif ch == 'email':
                self._send_email(alert, payload)
            elif ch == 'telegram':
                self._send_telegram(alert, payload)

    def _send_email(self, alert: Alert, payload: Dict):
        # send only if SMTP env configured
        smtp_host = os.environ.get('ALERT_SMTP_HOST')
        smtp_user = os.environ.get('ALERT_SMTP_USER')
        smtp_pass = os.environ.get('ALERT_SMTP_PASS')
        to_addr = os.environ.get('ALERT_EMAIL_TO')
        if not smtp_host or not to_addr:
            print('[ALERT] Email not sent; SMTP not configured')
            return
        # lightweight send (no TLS complexity here)
        try:
            server = smtplib.SMTP(smtp_host)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            msg = f"Subject: Alert {alert.name}\n\n{json.dumps(payload)}"
            server.sendmail(smtp_user, to_addr, msg)
            server.quit()
        except Exception as e:
            print('[ALERT] Email send failed:', e)

    def _send_telegram(self, alert: Alert, payload: Dict):
        # send only if TELEGRAM_BOT_TOKEN & CHAT_ID present
        bot = os.environ.get('ALERT_TELEGRAM_BOT')
        chat = os.environ.get('ALERT_TELEGRAM_CHAT')
        if not bot or not chat:
            print('[ALERT] Telegram not sent; config missing')
            return
        # avoid external network in demo environment - user can enable
        print(f"[ALERT] Would send Telegram to {chat}: {payload}")


# singleton
alert_manager = AlertManager()


def _safe_eval_condition(expr: str, metrics: Dict[str, Any]) -> bool:
    """Evaluate a boolean expression safely against a metrics dict.

    Allowed constructs: comparisons, boolean ops, arithmetic, literals, subscripts on `metrics`,
    and `metrics.get(...)`. A small set of builtin functions is allowed (min, max, abs, round).
    Any other AST node will raise ValueError.
    """
    allowed_funcs = {"min", "max", "abs", "round"}
    allowed_metric_methods = {"get"}

    try:
        node: AST = ast.parse(expr, mode="eval")
    except Exception:
        raise

    def _check(n: AST) -> bool:
        # Expression wrapper
        if isinstance(n, ast.Expression):
            return _check(n.body)
        # Boolean ops: and/or
        if isinstance(n, ast.BoolOp):
            return all(_check(v) for v in n.values)
        # Binary arithmetic
        if isinstance(n, ast.BinOp):
            if not isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv)):
                return False
            return _check(n.left) and _check(n.right)
        # Unary ops: +,-,not
        if isinstance(n, ast.UnaryOp):
            if not isinstance(n.op, (ast.UAdd, ast.USub, ast.Not)):
                return False
            return _check(n.operand)
        # Comparisons
        if isinstance(n, ast.Compare):
            if not _check(n.left):
                return False
            for comp in n.comparators:
                if not _check(comp):
                    return False
            # allow normal comparisons
            return all(isinstance(op, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot)) for op in n.ops)
        # Calls: allow metrics.get(...) and a small whitelist of functions
        if isinstance(n, ast.Call):
            # metrics.get(...) => func is Attribute(value=Name('metrics'), attr='get')
            if isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'metrics':
                if n.func.attr not in allowed_metric_methods:
                    return False
                for a in n.args:
                    if not _check(a):
                        return False
                for kw in n.keywords:
                    if not _check(kw.value):
                        return False
                return True
            # allowed builtin functions
            if isinstance(n.func, ast.Name) and n.func.id in allowed_funcs:
                for a in n.args:
                    if not _check(a):
                        return False
                return True
            return False
        # Names: only 'metrics' or allowed functions
        if isinstance(n, ast.Name):
            return n.id == 'metrics' or n.id in allowed_funcs or n.id in ('True', 'False')
        # Subscript: metrics['sharpe']
        if isinstance(n, ast.Subscript):
            return _check(n.value) and _check(n.slice)
        if isinstance(n, ast.Index):
            return _check(n.value)
        # Constant / Num / Str
        if isinstance(n, ast.Constant):
            return True
        # Containers
        if isinstance(n, (ast.List, ast.Tuple, ast.Set)):
            return all(_check(e) for e in n.elts)
        if isinstance(n, ast.Dict):
            return all(_check(k) and _check(v) for k, v in zip(n.keys, n.values))
        # Attributes are only allowed as metrics.get handled above
        return False

    if not _check(node):
        raise ValueError("Unsafe or unsupported expression")

    # safe evaluation environment
    safe_globals = {"__builtins__": None}
    safe_locals = {"metrics": metrics, "min": min, "max": max, "abs": abs, "round": round}
    return bool(eval(compile(node, "<safe_expr>", "eval"), safe_globals, safe_locals))
