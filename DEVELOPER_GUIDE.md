# GummySearch Developer Guide

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
│
├── PROJECT_OVERVIEW.md     # High-level project overview
└── DEVELOPER_GUIDE.md     # This guide
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Reddit API credentials
- OpenAI API key

### Environment Setup

1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

2. Frontend Setup
```bash
cd frontend
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your credentials
```

3. Database Setup
```bash
# In backend directory with venv activated
alembic upgrade head
```

## Development Workflow

### Starting the Development Servers

1. Always kill existing servers first:
```bash
pkill -f "uvicorn" && pkill -f "next"
```

2. Start backend server (from backend directory):
```bash
uvicorn app.main:app --reload --port 8001
```

3. Start frontend server (from frontend directory):
```bash
npm run dev
```

### Key Development Guidelines

1. **Database Changes**
   - Create new migrations: `alembic revision --autogenerate -m "description"`
   - Apply migrations: `alembic upgrade head`
   - Always test migrations both up and down

2. **API Development**
   - Routes go in `backend/app/routers/`
   - Business logic goes in `backend/app/services/`
   - Models in `backend/app/models/`
   - Schemas in `backend/app/schemas/`

3. **Frontend Development**
   - Pages in `frontend/src/app/`
   - Reusable components in `frontend/src/components/`
   - API services in `frontend/src/services/`
   - Types in `frontend/src/types/`

4. **Testing**
   - Backend tests in `backend/tests/`
   - Run tests: `pytest` from backend directory
   - Frontend tests: `npm test` from frontend directory

## Key Concepts

### Authentication
- JWT-based authentication
- Tokens stored in HTTP-only cookies
- Protected routes use FastAPI dependencies

### Data Flow
1. User creates audience
2. Backend collects posts asynchronously
3. Posts analyzed and categorized into themes
4. Frontend displays themes and enables AI analysis

### Theme System
- Posts automatically categorized based on metrics and keywords
- Theme matches stored in post_analysis table
- Posts can belong to multiple themes
- AI-powered Q&A based on themed content

### Background Tasks
- Post collection runs asynchronously
- Scheduled tasks update data hourly
- Progress tracking through WebSocket updates

## Common Issues & Solutions

1. **Port Conflicts**
   - Backend must run on 8001
   - Frontend defaults to 3000, falls back to 3001
   - Kill existing processes before starting servers

2. **Database Issues**
   - Check PostgreSQL service is running
   - Verify connection string in .env
   - Run migrations: `alembic upgrade head`

3. **API Rate Limits**
   - Reddit: Max 60 requests/minute
   - OpenAI: Depends on subscription

## Best Practices

1. **Code Style**
   - Backend: PEP 8
   - Frontend: ESLint config
   - Use type hints everywhere
   - Document complex functions

2. **Git Workflow**
   - Branch naming: feature/, bugfix/, hotfix/
   - Commit messages: conventional commits
   - PR template in .github/

3. **Error Handling**
   - Use custom exception classes
   - Proper HTTP status codes
   - Consistent error response format

4. **Performance**
   - Use async/await properly
   - Implement caching where appropriate
   - Optimize database queries
   - Lazy load components

## Deployment

1. **Production Setup**
   - Use production environment variables
   - Enable CORS properly
   - Set up proper logging
   - Configure rate limiting

2. **Monitoring**
   - Check server logs
   - Monitor database performance
   - Track API rate limits
   - Watch for memory usage

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [AsyncPRAW Documentation](https://asyncpraw.readthedocs.io/)
- [Project Overview](PROJECT_OVERVIEW.md)
- [Testing Plan](testing_plan.md) 