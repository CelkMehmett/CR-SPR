#!/usr/bin/env python3
"""Smoke test for dashboards endpoints using Flask test client."""

import sys
sys.path.insert(0, '.')

from poc.presentation_v2 import server

app = server.app

with app.test_client() as c:
    resp = c.get('/dashboards/')
    print('GET /dashboards/ ->', resp.status_code)
    # If HTML, print a short preview
    content_type = resp.headers.get('Content-Type','')
    print('Content-Type:', content_type)
    data = resp.get_data(as_text=True)
    print(data[:400])
