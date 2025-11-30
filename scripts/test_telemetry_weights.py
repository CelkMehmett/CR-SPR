#!/usr/bin/env python3
"""Smoke test for /telemetry/weights endpoint using Flask test client."""

import sys
sys.path.insert(0, '.')

from poc.presentation_v2 import server

app = server.app

with app.test_client() as c:
    resp = c.get('/telemetry/weights')
    print('GET /telemetry/weights ->', resp.status_code)
    print('Content-Type:', resp.headers.get('Content-Type'))
    print(resp.get_data(as_text=True)[:800])
