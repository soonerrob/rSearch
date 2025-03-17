# GummySearch - Reddit Audience Research Tool

GummySearch is a powerful audience research tool that helps you gather insights from Reddit communities. It collects and analyzes posts and comments, identifies themes and trends, and provides AI-powered insights about your target audience.

## Features

- **Audience Creation**: Create custom audiences by selecting relevant subreddits
- **Data Collection**: Automatically collect posts and threaded comments from selected subreddits
- **Theme Analysis**: Organize content into themed categories with engagement scoring
- **AI Insights**: Ask questions about your audience using GPT-4 powered analysis
- **Performance Optimization**: Smart caching and context preparation for fast responses

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Reddit API credentials
- OpenAI API key

### Backend Setup

1. Create and activate a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
DATABASE_URL=postgresql://user:password@localhost:5432/gummysearch
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_user_agent
OPENAI_API_KEY=your_openai_key
```

4. Initialize the database:
```bash
alembic upgrade head
```

5. Start the backend server:
```bash
uvicorn app.main:app --reload --port 8001
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

3. Start the frontend server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Documentation

- [Project Overview](PROJECT_OVERVIEW.md): Detailed system architecture and features
- [AI Service Documentation](docs/AI_SERVICE.md): AI analysis capabilities and usage
- API Documentation: Available at http://localhost:8001/docs when backend is running

## Development

### Running Tests

Backend tests:
```bash
cd backend
./run_tests.sh
```

Frontend tests:
```bash
cd frontend
npm test
```

### Code Style

Backend:
- Black for Python formatting
- Flake8 for linting
- MyPy for type checking

Frontend:
- Prettier for formatting
- ESLint for linting
- TypeScript for type safety

## License

MIT License - see LICENSE file for details 