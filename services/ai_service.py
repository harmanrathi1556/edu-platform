import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def solve_doubt(question):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"Solve step-by-step:\n{question}"}
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        data = response.json()

        answer = data['candidates'][0]['content']['parts'][0]['text']

        return answer

    except Exception as e:
        return f"Error: {str(e)}"
