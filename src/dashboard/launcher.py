"""
🚀 CRISPR-FinAI Dashboard Launcher

Quick launcher script for the advanced visualization dashboard.
Run this to start the interactive web interface.

From command line insights to visual intelligence.
"""

import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = ['streamlit', 'plotly', 'pandas', 'numpy']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("📦 Installing required packages...")

        for package in missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

        print("✅ All packages installed successfully!")
    else:
        print("✅ All required packages are installed.")

def launch_dashboard():
    """Launch the Streamlit dashboard."""
    # Get the path to the dashboard script
    dashboard_path = Path(__file__).parent / "streamlit_app.py"

    if not dashboard_path.exists():
        print(f"❌ Dashboard script not found at: {dashboard_path}")
        return

    print("🚀 Launching CRISPR-FinAI Dashboard...")
    print("📊 Opening interactive web interface...")

    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable,
            '-m',
            'streamlit',
            'run',
            str(dashboard_path),
            '--server.port=8501',
            '--server.headless=false'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user.")
    except Exception as e:
        print(f"❌ Error launching dashboard: {str(e)}")

if __name__ == "__main__":
    print("🧬 CRISPR-FinAI Dashboard Launcher")
    print("=" * 40)

    # Check dependencies
    check_dependencies()

    # Launch dashboard
    launch_dashboard()
