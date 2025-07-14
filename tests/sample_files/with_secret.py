#!/usr/bin/env python3
"""Sample Python file with a secret for testing trufflehog detection."""

import requests

# This is a fake secret that should be detected by trufflehog
# Real-looking GitHub token pattern
GITHUB_TOKEN = "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"
# API key pattern that should trigger detection
DATABASE_URL = "postgresql://user:mypassword123@localhost:5432/mydb"

def get_user_data():
    """Function that uses the fake credentials."""
    # This would normally be a security issue in real code
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    return requests.get("https://api.github.com/user", headers=headers)

if __name__ == "__main__":
    print("This file contains test secrets for security scanning validation")