# Flashcard Scheduler API (3-Grade Spaced Repetition)

This project implements a **spaced-repetition learning scheduler API** based on the coding challenge provided by **Langaku / GBP Inc.**  
The system supports **three learning grades** and schedules review intervals dynamically based on user performance.

---

## Features

- Record and schedule flashcard reviews with **3 difficulty ratings**:
  - `0` → Don't remember → Retry within **1 minute**
  - `1` → Remembered with effort → Moderate interval
  - `2` → Knew instantly → Longest interval
- Monotonic spacing (intervals never shorten)
- Simple API with idempotent logic
- Get all due cards before a specific time
- Designed with Django REST Framework

---

## Tech Stack

- **Python** 3.13+
- **Django** 5.2+
- **Django REST Framework**
- **SQLite / PostgreSQL**
- **pytest** for automated testing

---

## Project Structure

flashcard_api/
├── scheduler/
│ ├── models.py
│ ├── views.py
│ ├── serializers.py
│ └── urls.py
├── flashcard_api/
│ ├── settings.py
│ ├── urls.py
├── manage.py
└── README.md

yaml
Copy code

---

## Algorithm Logic

### 1️⃣ Rating = 0 ("Don't remember")
- Immediate retry within **1 minute**.
- Resets difficulty level to base.

### 2️⃣ Rating = 1 ("Remembered with effort")
- Schedules next review using a **medium interval**, e.g.:
next_interval = last_interval * 2

markdown
Copy code
- Ensures interval does not decrease.

### 3️⃣ Rating = 2 ("Knew instantly")
- Schedules the **longest interval**:
next_interval = last_interval * 3

yaml
Copy code
- Suitable for confident retention.

All intervals stored in seconds, calculated dynamically per user+card combination.

---

## API Endpoints

### 1️⃣ POST `/api/reviews/`
Records a review and calculates the next due time.

**Request Example:**
```json
{
"user_id": "10",
"card_id": "1",
"rating": 2
}
Response:

json
Copy code
{
  "user_id": "10",
  "card_id": "1",
  "next_review_at": "2025-11-23T20:06:31Z",
  "last_interval_seconds": 2592000
}
2️⃣ GET /api/users/{user_id}/due-cards/?until=2025-10-30T00:00:00Z
Fetch all cards that are due before a specific timestamp.

Response Example:

json
Copy code
[]
 Running Locally
bash
Copy code









## Clone repo
git clone https://github.com/nihalraza369/flashcard_scheduler.git
cd flashcard_scheduler

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Run server
python manage.py runserver
Then visit 👉 http://127.0.0.1:8000/api/reviews/

 Testing
To run tests:

bash
Copy code
python manage.py test
All tests passed successfully ✅

nginx
Copy code
Ran 4 tests in 0.072s
OK
💡 Future Improvements
Add authentication for multi-user access.

Optimize intervals with AI-based prediction (Leitner/SM2).

Add front-end dashboard for reviewing progress.

