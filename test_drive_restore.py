#!/usr/bin/env python3
"""
Test script para verificar la funcionalidad de restore desde Google Drive
"""

import requests
import json

def test_restore_drive_endpoint():
    """Test del endpoint /maintenance/api/restore-drive"""
    
    # URL del endpoint
    url = "http://localhost:5001/maintenance/api/restore-drive"
    
    # Datos de prueba
    test_data = {
        "file_id": "test_file_id_123", 
        "file_name": "test_backup.json"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🧪 Testing restore-drive endpoint...")
        print(f"URL: {url}")
        print(f"Data: {test_data}")
        
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
            
        return response.status_code, response.text
        
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return None, str(e)

if __name__ == "__main__":
    test_restore_drive_endpoint()
