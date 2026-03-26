import sys 
import json

def json_response(success: bool, message: str, data=None):
    """Formats a JSON response for Tauri"""
    response = {"success": success, "message": message, "data": data}
    print(json.dumps(response))  # Print as JSON for Tauri to capture
    sys.exit(0 if success else 1)  # Ensure correct exit codes
