from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import random

from app.rate_limiter import rate_limiter

app = FastAPI(title="Wonderful and Mysterious API v3.0")

# Serve static files (CSS, JS, images) from app/static/
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# In-memory database
db = {"favorites": []}


class FavoriteItem(BaseModel):
    id: int


class SubmitPayload(BaseModel):
    user: str
    data: dict


# ---------------------------
# Hardcoded Data Pools
# ---------------------------

WEATHER_DATA = {
    "seattle": {
        "city": "Seattle", "region": "Washington, US",
        "temp_c": 13, "temp_f": 55, "condition": "Overcast",
        "humidity_pct": 82, "wind_mph": 11, "visibility_miles": 7, "uv_index": 2,
    },
    "miami": {
        "city": "Miami", "region": "Florida, US",
        "temp_c": 31, "temp_f": 88, "condition": "Partly Cloudy",
        "humidity_pct": 74, "wind_mph": 14, "visibility_miles": 10, "uv_index": 9,
    },
    "new york": {
        "city": "New York", "region": "New York, US",
        "temp_c": 18, "temp_f": 64, "condition": "Sunny",
        "humidity_pct": 55, "wind_mph": 9, "visibility_miles": 10, "uv_index": 5,
    },
    "chicago": {
        "city": "Chicago", "region": "Illinois, US",
        "temp_c": 10, "temp_f": 50, "condition": "Windy with Clouds",
        "humidity_pct": 68, "wind_mph": 22, "visibility_miles": 9, "uv_index": 3,
    },
    "los angeles": {
        "city": "Los Angeles", "region": "California, US",
        "temp_c": 26, "temp_f": 79, "condition": "Sunny",
        "humidity_pct": 38, "wind_mph": 6, "visibility_miles": 10, "uv_index": 8,
    },
    "denver": {
        "city": "Denver", "region": "Colorado, US",
        "temp_c": 15, "temp_f": 59, "condition": "Clear",
        "humidity_pct": 30, "wind_mph": 13, "visibility_miles": 10, "uv_index": 6,
    },
    "austin": {
        "city": "Austin", "region": "Texas, US",
        "temp_c": 28, "temp_f": 82, "condition": "Hot and Sunny",
        "humidity_pct": 48, "wind_mph": 10, "visibility_miles": 10, "uv_index": 9,
    },
    "boston": {
        "city": "Boston", "region": "Massachusetts, US",
        "temp_c": 12, "temp_f": 54, "condition": "Light Rain",
        "humidity_pct": 88, "wind_mph": 17, "visibility_miles": 5, "uv_index": 1,
    },
    "phoenix": {
        "city": "Phoenix", "region": "Arizona, US",
        "temp_c": 38, "temp_f": 100, "condition": "Blazing Sun",
        "humidity_pct": 14, "wind_mph": 5, "visibility_miles": 10, "uv_index": 11,
    },
    "portland": {
        "city": "Portland", "region": "Oregon, US",
        "temp_c": 14, "temp_f": 57, "condition": "Drizzle",
        "humidity_pct": 85, "wind_mph": 8, "visibility_miles": 6, "uv_index": 2,
    },
}

DEFAULT_WEATHER = {
    "city": None,
    "region": "Unknown Region",
    "temp_c": 20, "temp_f": 68, "condition": "Clear",
    "humidity_pct": 60, "wind_mph": 8, "visibility_miles": 10, "uv_index": 4,
}

INSIGHTS = {
    "general": [
        "Small, consistent actions compound into extraordinary results over time.",
        "Clarity of purpose is more powerful than intensity of effort.",
        "The best time to build a habit is before you need it.",
        "Simplicity on the other side of complexity is wisdom.",
        "Progress thrives in environments where feedback is fast and honest.",
        "Most obstacles are narrower than they appear from a distance.",
        "Understanding the problem deeply is already half the solution.",
        "Patience and persistence are the twin engines of lasting achievement.",
    ],
    "technology": [
        "The most scalable systems are the ones built to be replaced.",
        "Readable code is a love letter to the next developer, including future you.",
        "Premature optimization is the root of many unnecessary rewrites.",
        "A good API is one that makes the wrong thing hard to do.",
        "Tests don't just catch bugs — they document intent.",
        "Latency is a feature. Fast systems feel trustworthy.",
        "The best infrastructure is the kind users never think about.",
        "Complexity is rarely introduced all at once; it accumulates one shortcut at a time.",
    ],
    "productivity": [
        "Protect your deep work time like a scarce resource — because it is.",
        "Done and iterable beats perfect and delayed every time.",
        "Energy management matters more than time management.",
        "The clearest signal of priority is where your attention actually goes.",
        "Reduce friction for the behaviors you want to repeat.",
        "A short list of important tasks beats a long list of urgent ones.",
        "Rest is not the absence of productivity; it is a prerequisite for it.",
        "The two-minute rule: if it takes less than two minutes, do it now.",
    ],
    "leadership": [
        "Great leaders make their team's work visible before making themselves visible.",
        "Trust is built in drops and lost in buckets.",
        "The best question a leader can ask is: what is blocking you?",
        "Clarity reduces anxiety. Be explicit about expectations.",
        "Feedback is a gift — the quality of your relationships determines how often it's given.",
        "Delegate outcomes, not just tasks.",
        "Psychological safety is not about being nice. It's about being honest safely.",
        "A leader's job is to multiply the capacity of those around them.",
    ],
    "creativity": [
        "Constraints are not the enemy of creativity — they are its scaffold.",
        "The first idea is rarely the best one, but you need it to get to the good ones.",
        "Creative breakthroughs often hide just past the point of frustration.",
        "Boredom is the incubator of original thought.",
        "Steal like an artist: absorb influences, then synthesize them into something new.",
        "The best creative work usually starts with genuine curiosity, not a brief.",
        "Ship early drafts to real people. Their reactions are your compass.",
        "Creativity expands to fill the time allotted — set tighter deadlines.",
    ],
}

FORTUNES = [
    {"fortune": "A quiet moment today holds the seed of tomorrow's breakthrough.",
     "lucky_number": 7, "lucky_color": "Indigo", "advice": "Slow down before the next decision."},
    {"fortune": "The answer you have been searching for is closer than it appears.",
     "lucky_number": 42, "lucky_color": "Gold", "advice": "Look inward before looking outward."},
    {"fortune": "A conversation you almost didn't have will change everything.",
     "lucky_number": 13, "lucky_color": "Crimson", "advice": "Say yes to the unexpected invitation."},
    {"fortune": "Your next great idea will arrive when you stop looking for it.",
     "lucky_number": 3, "lucky_color": "Sage Green", "advice": "Schedule unstructured time this week."},
    {"fortune": "Obstacles ahead are smaller than the shadow they cast.",
     "lucky_number": 99, "lucky_color": "Silver", "advice": "Take the first step before you feel ready."},
    {"fortune": "Something you built long ago is about to pay dividends.",
     "lucky_number": 21, "lucky_color": "Amber", "advice": "Revisit a project you set aside."},
    {"fortune": "The door you keep passing is the one worth opening.",
     "lucky_number": 8, "lucky_color": "Teal", "advice": "Act on the thing you have been deferring."},
    {"fortune": "Fortune favors those who prepare in the quiet before the storm.",
     "lucky_number": 17, "lucky_color": "Navy", "advice": "Invest in prevention over reaction."},
    {"fortune": "A small kindness you offer today will return magnified.",
     "lucky_number": 5, "lucky_color": "Rose", "advice": "Reach out to someone you haven't spoken to in a while."},
    {"fortune": "The version of success you imagined last year no longer fits who you are.",
     "lucky_number": 33, "lucky_color": "Copper", "advice": "Redefine the goal before chasing it harder."},
    {"fortune": "Clarity is coming. Be patient with the fog.",
     "lucky_number": 11, "lucky_color": "Pearl", "advice": "Write down what you know and what you don't."},
    {"fortune": "The collaboration you have been avoiding is the one that will unlock you.",
     "lucky_number": 64, "lucky_color": "Violet", "advice": "Reach across a gap you've been maintaining."},
]


# ---------------------------
# Rate Limiting Middleware
# ---------------------------

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too Many Requests"},
        )
    return await call_next(request)


# ---------------------------
# Landing Page
# ---------------------------

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    with open("app/static/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)


# ---------------------------
# API Endpoints
# ---------------------------

@app.get("/api/weather")
async def get_weather(city: str = "Seattle"):
    key = city.strip().lower()
    if key in WEATHER_DATA:
        return WEATHER_DATA[key]
    response = DEFAULT_WEATHER.copy()
    response["city"] = city.title()
    return response


@app.get("/api/insight")
async def get_insight(topic: str = "general"):
    key = topic.strip().lower()
    pool = INSIGHTS.get(key, INSIGHTS["general"])
    return {
        "id": random.randint(100, 999),
        "topic": key if key in INSIGHTS else "general",
        "insight": random.choice(pool),
        "available_topics": list(INSIGHTS.keys()),
    }


@app.get("/api/fortune")
async def get_fortune():
    fortune = random.choice(FORTUNES)
    return {"id": random.randint(1, 100), **fortune}


@app.post("/api/submit", status_code=201)
async def post_submit(payload: SubmitPayload):
    return {"status": "Created", "received": payload}


@app.post("/api/favorites", status_code=201)
async def add_favorite(item: FavoriteItem):
    db["favorites"].append(item.id)
    return {"message": "Saved", "current_favorites": db["favorites"]}


@app.get("/api/favorites")
async def get_favorites():
    return {"favorites": db["favorites"]}
