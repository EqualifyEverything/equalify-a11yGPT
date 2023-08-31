import secrets
import requests
from a11yGPT_package.models import User, MonthlySpend, Session
from a11yGPT_package import db
from werkzeug.security import generate_password_hash
import json
import re
import openai
openai.api_key = "YOUR_API_KEY"

def generate_api_token():
    return secrets.token_hex(32)

def populate_sample_data():
    db.create_all()

    # Check if the sample user already exists
    sample_user = User.query.filter_by(email='blake@decubing.com').first()
    
    if not sample_user:
        # Create the sample user
        sample_user = User(
            email='blake@decubing.com',
            password=generate_password_hash('PassSample!', method='sha256'),
            api_token=generate_api_token()
        )
        db.session.add(sample_user)
        db.session.commit()
    
    # Add sample monthly spends for the sample user
    sample_monthly_spends = [
        {'month': '2023-01', 'spend': 150.0},
        {'month': '2023-02', 'spend': 200.0},
        {'month': '2023-03', 'spend': 180.0},
        {'month': '2023-04', 'spend': 210.0}
    ]

    for spend_data in sample_monthly_spends:
        # Check if the monthly spend already exists
        monthly_spend = MonthlySpend.query.filter_by(user_id=sample_user.id, month=spend_data['month']).first()

        if not monthly_spend:
            # Create and add the monthly spend
            monthly_spend = MonthlySpend(
                user_id=sample_user.id,
                month=spend_data['month'],
                spend=spend_data['spend']
            )
            db.session.add(monthly_spend)
            db.session.commit()

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def scrape_html(session_id, url):
    session = Session.query.get(session_id)

    # Log the initial message
    session.status = "Scraping HTML"
    db.session.commit()

    # # Send the URL to the ScrapingBee API (replace YOUR_API_KEY with your actual API key)
    scrapingbee_response = requests.get(
        "https://app.scrapingbee.com/api/v1",
        params={
            "api_key": "YOUR_API_KEY",
            "url": url
        }
    )

    if scrapingbee_response.status_code == 200:
        html = scrapingbee_response.text
    else:
        session.status = f"Failed"
        session.results = f"ScrapingBee request failed with status code {scrapingbee_response.status_code}"
        html = ""

    db.session.commit()
    
    # html = "<p>hello</p><img />"

    return html

def run_gpt(session_id, html):
    session = Session.query.get(session_id)

    session.status = "Running AI"
    db.session.commit()

    # Prepare the messages. Here are the other 11:
    # 2) The reading and navigation order (determined by code order) is logical and intuitive. (1.3.2)
    # 13) Instructions do not rely upon shape, size, or visual location (e.g., 'Click the square icon to continue' or 'Instructions are in the right-hand column'). (1.3.3)
    # 14) Orientation of web content is not restricted to only portrait or landscape, unless a specific orientation is necessary. (1.3.4)
    # 15) Input fields that collect certain types of user information have an appropriate autocomplete attribute defined. (1.3.5)
    # 16) HTML5 regions or ARIA landmarks are used to identify page regions. (1.3.6)
    # 17) Color is not used as the sole method of conveying content or distinguishing visual elements. (1.4.1)
    # 18) A mechanism is provided to stop, pause, mute, or adjust volume for audio that automatically plays on a page for more than 3 seconds. (1.4.2)
    # 19) Text and images of text have a contrast ratio of at least 4.5:1. (1.4.3)
    # 20) The page is readable and functional when the page is zoomed to 200%. Note: 1.4.10 introduces a much higher requirement for zoomed content. (1.4.4)
    # 21) If the same visual presentation can be made using text alone, an image is not used to present that text. (1.4.5)

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": f"""Analyze the following HTML code against the provided accessibility standards and return minified JSON output with pass, fail, or null values for each standard, along with reasoning for its decision. Do not skip a standard. Include no other response.
            Sample JSON output:
            {{"standard": [{{"id": "1.1.1", "result": "pass", "reason": "The image has an appropriate and equivalent alternative text."}}, {{"id": "2.4.2", "result": "fail", "reason": "The page title, 'Untitled Document', is not descriptive and informative."}}]}}

            Accessibility Standards:
            `   1) Images, form image buttons, and image map hot spots have appropriate, equivalent alternative text. (1.1.1)
                2) A transcript of relevant content is provided on the page under a heading that reads like "transcript" for non-live audio-only (audio podcasts, MP3 files, etc.). (1.2.1)
                3) Synchronized captions are provided for non-live video (YouTube videos, etc.). (1.2.2)
                4) A transcript or audio description is provided for non-live video. (1.2.3)
                5) Synchronized captions are provided for live media that contains audio (audio-only broadcasts, webcasts, video conferences, etc.) (1.2.4)
                6) Audio descriptions are provided for non-live video. (1.2.5)
                7) A sign language video is provided for media that contains audio. (1.2.6)
                8) When audio description cannot be added to video due to audio timing (e.g., insufficient pauses in the audio), an alternative version of the video with pauses that allow audio descriptions is provided. (1.2.7)
                9) A transcript is provided for prerecorded media that has a video track. For optimal accessibility, WebAIM strongly recommends transcripts for all multimedia. (1.2.8)
                10) A descriptive text transcript (e.g., the script of the live audio) is provided for live content that has audio. (1.2.9)
                11) Semantic markup is used to designate headings (<h1>), regions/landmarks, lists (<ul>, <ol>, and <dl>), emphasized or special text (<strong>, <code>, <abbr>, <blockquote>, for example), etc. Semantic markup is used appropriately. (1.3.1)
            HTML Code:
            {html}"""
        }
    ]

    # Call the ChatGPT API to get the response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Update the GPT-3 model to use
        messages=messages,
    )

    # Extract the response text from the API response
    if 'choices' in response and response['choices']:
        text = response['choices'][0]['message']['content'].strip()
    else:
        text = "Error: No response from GPT-3 API"

    # Convert the response text to a Python dictionary
    results_dict = json.loads(text)

    # Update the session results and status
    session.results = results_dict
    session.status = html
    db.session.commit()
