import speech_recognition as sr
import random
import requests
import json
import string
import webbrowser # Import for opening the audio preview in the browser
import sys 

# --- Configuration ---
# IMPORTANT: This key is required to search the FreeSound database.
# Key provided by user (Client ID)
FREESOUND_API_KEY = "LCRU3iy7x8OKdQC5XjXQdQQ6xIb0p3jrdaKBaWMY"

def speech_to_text(limit_duration: float) -> str | None:
    """
    Listens to the microphone for a randomly limited time and converts the speech to text.

    Args:
        limit_duration (float): The maximum duration (in seconds) to record after speech starts.

    Returns:
        str: The transcribed text, or None if an error occurs.
    """
    r = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        # Adjust for ambient noise for better accuracy
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            # timeout=5: Max time to wait for the user to START speaking.
            # phrase_time_limit: Max time to record AFTER speech starts.
            # The random duration is used here to cut off the phrase and capture the "last word".
            audio = r.listen(source, timeout=5, phrase_time_limit=limit_duration)
        except sr.WaitTimeoutError:
            # This error occurs if no speech is detected within the initial 5-second timeout.
            print("No speech detected within the initial timeout window.")
            return None

    print("Processing audio...")

    try:
        # Use Google's free Web Speech API
        text = r.recognize_google(audio)
        print(f"\n✅ Transcription successful: \"{text}\"")
        return text.lower()
    except sr.UnknownValueError:
        print("❌ Could not understand audio (speech too quiet or unclear, or phrase limit was too short).")
        return None
    except sr.RequestError as e:
        print(f"❌ Could not request results from Google Speech Recognition service; {e}")
        return None

def select_random_word(text: str) -> str | None:
    """
    Cleans the transcribed text and selects the LAST word captured from the limited recording.

    Args:
        text (str): The transcribed text.

    Returns:
        str: The last selected word, or None if the text is empty.
    """
    # 1. Remove punctuation and convert to lowercase
    translator = str.maketrans('', '', string.punctuation)
    clean_text = text.translate(translator)

    # 2. Split into words and filter out empty strings
    words = [word for word in clean_text.split() if word]

    if not words:
        print("❌ No valid words found in the transcription after cleaning.")
        return None

    # 3. Select the LAST word captured from the list
    search_word = words[-1]
    print(f"\n🎯 Selected the last word captured: \"{search_word}\"")
    return search_word

def search_freesound(query_word: str):
    """
    Searches the FreeSound API using the randomly selected word, prints the result,
    and opens the direct MP3 preview in the browser.
    
    This function now fetches up to 10 results and randomly selects one from the list.
    """
    if FREESOUND_API_KEY in ["YOUR_CLIENT_ID_GOES_HERE", "YOUR_FREESOUND_API_KEY"]:
        print("\nFATAL ERROR: FreeSound API key is missing or invalid.")
        return

    BASE_URL = "https://freesound.org/apiv2/search/text/"
    
    # Request the top 10 results to enable random selection
    RESULTS_TO_FETCH = 10
    
    params = {
        "query": query_word,
        "token": FREESOUND_API_KEY,
        # Request 'previews' field to get a direct MP3 URL for playback
        "fields": "name,url,username,previews",
        "page_size": RESULTS_TO_FETCH # Retrieve more results
    }

    print(f"\nSearching FreeSound for top {RESULTS_TO_FETCH} sounds related to \"{query_word}\"...")

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        results = data.get('results', [])

        if results:
            # RANDOMLY select one result from the list
            selected_result = random.choice(results)
            
            # The preview MP3 link is nested in the 'previews' field
            preview_url = selected_result.get('previews', {}).get('preview-hq-mp3')

            print(f"\n--- Randomly Selected Result for \"{query_word}\" (1 of {len(results)}) ---")
            print(f"1. Title: {selected_result.get('name', 'N/A')}")
            print(f"   Source Page: {selected_result.get('url', 'N/A')}")
            print(f"   Uploader: {selected_result.get('username', 'N/A')}")
            
            if preview_url:
                print("\n🎧 Opening sound preview in your default web browser now (in a new tab)...")
                webbrowser.open(preview_url)
            else:
                print("⚠️ Could not find a playable preview URL for the result.")
            
            print("\n-------------------------------------------")

        else:
            print(f"\n🤷 FreeSound search returned no results for \"{query_word}\".")
            print("Try saying a more common noun!")

    except requests.exceptions.HTTPError as err:
        print(f"\n❌ HTTP Error occurred: {err}")
        print("Check if your API key is valid or if the search query is too long/complex.")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ An error occurred during the API request: {e}")
    except json.JSONDecodeError:
        print("\n❌ Failed to decode the JSON response from FreeSound.")


if __name__ == "__main__":
    print("\n--- Speech-to-Text FreeSound Search Tool Started (Continuous Mode) ---")
    
    # Main infinite loop
    while True:
        print("\n\n=============================================")
        
        # Randomly generate the phrase time limit between 4.0 and 8.0 seconds
        random_duration = random.uniform(4.0, 8.0)
        print(f"🎤 Listening duration is randomly set to: {random_duration:.2f} seconds.")
        print("🎧 Please speak now to begin search...")
        
        # 1. Capture audio, using the random limit
        transcribed_text = speech_to_text(random_duration)

        if transcribed_text:
            # 2. Select last word
            search_term = select_random_word(transcribed_text)
            
            if search_term:
                # 3. Search and play sound
                search_freesound(search_term)
        else:
            print("\nNo full phrase captured. Returning to listening mode.")
