#!/usr/bin/env python3
"""
Simple runner script for the STC Query Assistant Streamlit app.
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit application"""
    try:
        # Check if streamlit is installed
        subprocess.check_call([sys.executable, "-c", "import streamlit"])
        
        # Set environment variable for better performance
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        
        # Run the Streamlit app
        print("🚀 Starting STC Query Assistant...")
        print("📱 Open your browser to the URL shown below")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except subprocess.CalledProcessError:
        print("❌ Streamlit is not installed. Please install it with:")
        print("   pip install streamlit")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error running the app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 