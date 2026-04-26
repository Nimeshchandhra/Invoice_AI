import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NVIDIA_API_KEY")

def generate_response(prompt):
    url = "https://integrate.api.nvidia.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta/llama-3.3-70b-instruct",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }



    response = requests.post(url, headers=headers, json=data, verify=False)
    
    if response.status_code != 200:
        print(f"API Error - Status Code: {response.status_code}")
        print(f"API Error - Response Text: {response.text}")
        response.raise_for_status() # This will stop the script safely and show the HTTP error
    result = response.json()

    ####

    return result["choices"][0]["message"]["content"]