import requests
import json
import time
from together import Together


# These API's are expensive, please add your own API keys. 
ELEVEN_LABS_API_KEY = "<Your API Key Here>"
BOOKING_COM_API_KEY = "<Your API Key Here>"
TOGETHER_API_KEY = "<Your API Key Here>"


ai_client = Together(api_key=TOGETHER_API_KEY)


def searchHotels(checkin, checkout, localairport, guests, rooms):
    url = "https://demandapi.booking.com/3.1/accommodations/search"

    payload = {
    "booker": {
        "country": "us",
        "platform": "desktop"
    },
    "checkin": checkin,
    "checkout": checkout,
    "airport": localairport,
    "guests": {
        "number_of_adults": guests,
        "number_of_rooms": rooms
    }
    }

    headers = {
    "Content-Type": "application/json",
    "X-Affiliate-Id": "0",
    "Authorization": "Bearer " + authkey
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    return data

def elevenlabs_tts(text, output_file, voice_id, stability=0.2, similarity_boost=0.85, retries=3, fallback_text=""):
    url = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "model_version": "eleven_turbo_v2_5"
        }
    }
    
    for attempt in range(retries):
        response = requests.post(url.format(voice_id=voice_id), headers=headers, json=data)
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"Saved TTS to {output_file}")
            return True
        else:
            print(f"Failed to generate TTS (attempt {attempt + 1}/{retries}): {response.text}")
            time.sleep(1)  

    print(f"Failed to generate TTS after {retries} attempts.")
    if fallback_text:
        print(f"Using fallback text for transition: {fallback_text}")
        fallback_data = {
            "text": fallback_text,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "model_version": "turbo_v2.5"
            }
        }
        response = requests.post(url.format(voice_id=voice_id), headers=headers, json=fallback_data)
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"Saved fallback TTS to {output_file}")
            return True

    return False

def getFireReport(prompt, firedata):
    resp = ai_client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        messages = [
            {"role":"assistant", "content":prompt},
            {"role":"user", "content":firedata}
        ]
    )
    return resp.choices[0].message.content
