# Reddit Audience Research Tool

A powerful tool for exploring and analyzing Reddit communities, helping users gain valuable insights into market trends, consumer behaviors, and brand perceptions.

## Features (Planned)

- Community Discovery
- Persona Exploration
- Trend Analysis
- Advanced Search
- Keyword Tracking
- AI Summarization

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a .env file in the backend directory with:
```
DATABASE_URL=postgresql://user:password@localhost:5432/reddit_research
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_app_name
OPENAI_API_KEY=your_openai_key
```

4. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create a .env.local file with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Start the development server:
```bash
npm run dev
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   └── main.py
└── frontend/
    ├── components/
    ├── pages/
    └── public/
```

## Development Status

🚧 Currently in active development 