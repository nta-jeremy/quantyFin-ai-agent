# QuantyFinAI Agent

AI-powered financial analysis and stock prediction system implementing a 7-agent RAG architecture using LangGraph for processing financial data, investing, stocks, and cryptocurrency analysis.

## 🚀 Features

- **Multi-Agent RAG System**: 7 specialized agents for financial analysis
- **Vector Database**: PostgreSQL with pgvector for efficient similarity search
- **Real-time Processing**: Streamlined data ingestion and analysis pipeline
- **Financial Intelligence**: Advanced sentiment analysis and prediction capabilities
- **Scalable Architecture**: Hexagonal architecture with clean separation of concerns

## 🏗️ Architecture

### 7-Agent RAG System
1. **Guard Agent**: Input validation and prompt injection protection
2. **Embedding Agent**: Document processing and vector embedding generation
3. **Retriever Agent**: Query transformation and data retrieval
4. **Search Agent**: External API integration and web search
5. **Analyze Agent**: Financial analysis and sentiment processing
6. **Predict Agent**: ML model predictions and forecasting
7. **Aggregator Agent**: Workflow orchestration and response synthesis

### Technology Stack
- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 16 with pgvector extension
- **Cache**: Redis for session management and rate limiting
- **Authentication**: Keycloak with JWT token management
- **Vector Search**: HNSW indexing for efficient similarity search
- **Containerization**: Docker and Docker Compose
- **LLM Integration**: OpenAI, Anthropic, Google, Deepseek APIs

## 🛠️ Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Poetry (dependency management)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd quantyFin-ai-agent
   ```

2. **Install dependencies:**
   ```bash
   # Using Poetry (recommended)
   poetry install

   # Or using pip
   pip install -e .
   ```

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the development environment:**
   ```bash
   # Start all services
   docker-compose up -d

   # Or start with hot reload
   docker-compose --profile dev up -d
   ```

5. **Verify the installation:**
   ```bash
   # Check database status
   docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT 'Database is ready' as status;"

   # Check pgvector installation
   docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
   ```

## 🔧 Database Setup

The system uses PostgreSQL with pgvector extension for vector operations. The database container includes:

- **pgvector 0.8.0**: For efficient vector similarity search
- **HNSW Indexing**: Hierarchical Navigable Small World indexes for fast search
- **Automatic Migrations**: Database schema initialization and migrations
- **Health Checks**: Container health monitoring

### Building the Database

```bash
# Build the pgvector database container
docker-compose build db

# Start the database
docker-compose up -d db

# Verify installation
docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

### Troubleshooting Database Issues

If you encounter build errors with pgvector:

1. **Clean build cache:**
   ```bash
   docker-compose down -v
   docker system prune -f
   docker-compose build db
   ```

2. **Test vector operations:**
   ```bash
   docker-compose exec db psql -U quantyfin -d quantyfin -c "
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE TABLE test_vectors (id SERIAL PRIMARY KEY, embedding VECTOR(3) NOT NULL);
   INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');
   SELECT id, embedding, embedding <-> '[0,0,0]' as distance FROM test_vectors ORDER BY distance;
   "
   ```

## 📚 API Documentation

Once the services are running, you can access:

- **API Documentation**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Database Health**: http://localhost:8000/api/v1/health
- **Keycloak Admin**: http://localhost:8080 (admin/admin123)

## 🔍 Testing

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test categories
poetry run pytest -m "unit"
poetry run pytest -m "integration"
poetry run pytest -m "e2e"
```

## 📊 Monitoring

### Health Checks
- **Application**: http://localhost:8000/api/v1/health
- **Database**: Docker health checks
- **Redis**: Available on port 6379
- **Keycloak**: Available on port 8080

### Logs
```bash
# View application logs
docker-compose logs -f app

# View database logs
docker-compose logs -f db

# View all service logs
docker-compose logs -f
```

## 🛡️ Security

- **Authentication**: JWT tokens with Keycloak integration
- **Authorization**: Role-based access control (RBAC)
- **Input Validation**: Pydantic models for all API inputs
- **Rate Limiting**: Redis-based rate limiting
- **CORS**: Proper cross-origin resource sharing configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

### Development Guidelines
- Follow the project's code style conventions
- Include tests for new features
- Update documentation as needed
- Use meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **pgvector**: Vector similarity search for PostgreSQL
- **LangGraph**: Multi-agent orchestration framework
- **FastAPI**: Modern, fast web framework
- **PostgreSQL**: Powerful open-source database
- **Redis**: High-performance in-memory data store

---

For questions or support, please open an issue in the repository or contact the development team.
