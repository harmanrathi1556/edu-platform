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

        print("RAW RESPONSE:", response.text)

        data = response.json()

        if "candidates" not in data:
            return "AI Error: " + str(data)

        return data['candidates'][0]['content']['parts'][0]['text']

    except Exception as e:
        return f"AI Error: {str(e)}"
