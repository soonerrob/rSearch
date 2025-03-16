# Reddit Audience Research Tool

A powerful tool for exploring and analyzing Reddit communities, helping users gain valuable insights into market trends, consumer behaviors, and brand perceptions.

## Documentation

This project includes comprehensive documentation split across several files:

1. **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - High-level overview of the project, its goals, and current status
2. **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Detailed guide for developers, including setup and best practices
3. **[TESTING_PLAN.md](TESTING_PLAN.md)** - Comprehensive testing procedures and requirements
4. **[TEST_RESULTS.md](TEST_RESULTS.md)** - Documentation of test outcomes and issues
5. **[FUTURE_PLANS.md](FUTURE_PLANS.md)** - Project roadmap and planned features
6. **[MIGRATION_PLAN.md](MIGRATION_PLAN.md)** - Details about the PRAW to AsyncPRAW migration
7. **[FEATURES.md](FEATURES.md)** - Current feature documentation
8. **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - Planned improvements and optimizations

## Features

- Community Discovery and Analysis
- Theme-based Content Organization
- AI-powered Insights
- Real-time Data Collection
- Advanced Search and Filtering
- Trend Analysis

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Reddit API credentials
- OpenAI API key

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
uvicorn app.main:app --reload --port 8001
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create a .env.local file with:
```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

3. Start the development server:
```bash
npm run dev
```

## Project Structure

```
gummysearch/
├── backend/                 # FastAPI backend
│   ├── alembic/            # Database migrations
│   ├── app/
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # API route handlers
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # Application entry point
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   ├── services/      # API client services
│   │   └── types/         # TypeScript types
│   └── package.json       # Node dependencies
```

## Development Status

🚧 Currently in active development

For detailed development instructions, please refer to the [Developer Guide](DEVELOPER_GUIDE.md). 