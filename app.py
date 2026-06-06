from flask import Flask, request, jsonify
import openai
import os
import requests
from datetime import datetime
import pytz

app = Flask(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Sydney,AU&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=5)
        data = r.json()
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        return f"Sydney weather: {desc}, {temp:.1f}°C (feels like {feels:.1f}°C), humidity {humidity}%"
    except:
        return "Weather unavailable right now."

def get_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=au&pageSize=5&apiKey={NEWS_API_KEY}"
        r = requests.get(url, timeout=5)
        articles = r.json().get("articles", [])
        headlines = [a["title"] for a in articles if a.get("title")][:5]
        return "Today's top Australian news: " + " | ".join(headlines)
    except:
        return "News unavailable right now."

def get_datetime():
    sydney_tz = pytz.timezone("Australia/Sydney")
    now = datetime.now(sydney_tz)
    return now.strftime("Today is %A, %d %B %Y. The time in Sydney is %I:%M %p.")

def build_alexa_response(text):
    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text
            },
            "shouldEndSession": True
        }
    })

@app.route("/", methods=["POST"])
def alexa_skill():
    body = request.get_json()
    request_type = body.get("request", {}).get("type", "")

    if request_type == "LaunchRequest":
        return build_alexa_response("Hi! Ask me anything. I'm powered by ChatGPT and I know today's weather, news, and the time.")

    if request_type == "IntentRequest":
        intent = body["request"]["intent"]["name"]

        if intent == "AskChatGPTIntent":
            user_query = body["request"]["intent"]["slots"]["query"]["value"]

            # Build real-time context
            weather_info = get_weather()
            news_info = get_news()
            datetime_info = get_datetime()

            system_prompt = f"""You are a smart, friendly voice assistant running on an Amazon Echo Show 5 in Sydney, Australia.
You have access to real-time information:
- {datetime_info}
- {weather_info}
- {news_info}

Rules:
- Keep answers concise and conversational — this is a voice response, not text.
- Don't use bullet points, markdown, or symbols like asterisks.
- If asked about weather, time, or news, use the real-time info above.
- If asked for more detail, you can give a slightly longer answer.
- Sound natural, like a helpful assistant."""

            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ]
            )
            answer = response.choices[0].message.content
            return build_alexa_response(answer)

    if request_type == "SessionEndedRequest":
        return jsonify({"version": "1.0", "response": {}})

    return build_alexa_response("Sorry, I didn't understand that.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
