"""Mutation Theater (Streamlit) - lightweight visualization of genome and mutations.

Run with:

    streamlit run apps/mutation_theater.py

The app is intentionally dependency-optional: if Streamlit or Plotly are missing it
will show a helpful message instead of crashing tests.
"""
from typing import List, Dict, Any
import os
import json


def load_demo_data():
    # Try to load mutations from a local file, otherwise synthesize demo data
    p = os.path.join(os.path.dirname(__file__), '..', 'data', 'mutations.json')
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    # synthesize demo
    genes = ['g1', 'g2', 'g3', 'g4', 'g5', 'g6']
    entries = []
    import time
    import random
    t0 = time.time()
    for i in range(12):
        g = random.choice(genes)
        entries.append({
            'ts': t0 + i * 10,
            'gene': g,
            'old': random.uniform(-1, 1),
            'new': random.uniform(-1, 1),
            'reward': random.uniform(-1, 1),
        })
    return {'genes': genes, 'entries': entries}


def render(genome_genes: List[str], entries: List[Dict[str, Any]]):
    try:
        import streamlit as st
    except Exception:
        print("Streamlit is not installed. Install with: pip install streamlit")
        return

    st.set_page_config(page_title="Mutation Theater", layout='wide')
    st.title("CRISPR-FinAI — Mutation Theater")

    cols = st.columns([3, 1])
    left, right = cols[0], cols[1]

    # sidebar controls
    with right:
        st.header("Controls")
        top_k = st.slider('Highlight recent mutations', 1, 10, 3)
        step = st.slider('Step through events', 0, max(0, len(entries)-1), len(entries)-1)

    # compute 3D positions for genes on a circle
    import math
    n = len(genome_genes)
    positions = {}
    for i, g in enumerate(genome_genes):
        theta = 2 * math.pi * i / max(1, n)
        positions[g] = (math.cos(theta), math.sin(theta), 0.2 * math.sin(2*theta))

    # prepare plotly visualization (optional)
    try:
        import plotly.graph_objects as go

        xs = [positions[g][0] for g in genome_genes]
        ys = [positions[g][1] for g in genome_genes]
        zs = [positions[g][2] for g in genome_genes]

        colors = ['lightblue'] * n
        recent = [e['gene'] for e in entries[max(0, step-top_k+1):step+1]] if entries else []
        for i, g in enumerate(genome_genes):
            if g in recent:
                colors[i] = 'red'

        fig = go.Figure(data=[
            go.Scatter3d(x=xs, y=ys, z=zs, mode='markers+text', marker=dict(size=10, color=colors), text=genome_genes, textposition='top center')
        ])
        fig.update_layout(height=600, margin=dict(l=0, r=0, t=40, b=0))
        left.plotly_chart(fig, use_container_width=True)
    except Exception:
        left.write("Install plotly for 3D visualization: pip install plotly")

    # Event timeline
    with left.expander('Mutation Timeline', expanded=True):
        for i, e in enumerate(entries):
            prefix = '👉 ' if i >= max(0, step-top_k+1) and i <= step else '   '
            left.write(f"{prefix}{i}. {e['gene']} {e['old']:.3f} → {e['new']:.3f} (r={e['reward']:.3f})")


if __name__ == '__main__':
    data = load_demo_data()
    try:
        render(data['genes'], data['entries'])
    except Exception as e:
        print('Error launching Mutation Theater:', e)
