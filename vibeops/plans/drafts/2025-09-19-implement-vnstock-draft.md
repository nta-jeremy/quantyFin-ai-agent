# Vnstock Integration Implementation Plan

## Overview of Current State

The QuantyFinAI Agent system is a sophisticated AI-powered financial analysis platform with:
- **7-Agent RAG Architecture**: Guard, Embedding, Retriever, Search, Analyze, Predict, Aggregator agents
- **Hexagonal Architecture**: Clean separation between domain, application, and infrastructure layers
- **Technology Stack**: FastAPI, PostgreSQL with pgvector, Redis, Keycloak, LangGraph
- **Current Focus**: International financial markets with generic financial data models

## Overview of Final State

After vnstock integration, the system will:
- **Support Vietnamese Markets**: HOSE, HNX, UPCOM exchanges with real-time and historical data
- **Multi-Source Data**: VCI, TCBS, MSN data providers for comprehensive coverage
- **Enhanced Financial Analysis**: Vietnamese-specific metrics, ratios, and market insights
- **Extended Agent Capabilities**: All agents will understand and process Vietnamese market data
- **Unified Data Models**: Seamless integration between international and Vietnamese financial data

## Files to Change

### 1. Core Domain Models (`app/core/domain/models.py`)
- Add Vietnamese market-specific models: `VietnameseStock`, `VietnameseCompany`, `VietnameseFinancialReport`
- Extend existing models with Vietnamese market attributes
- Add Vietnamese market exchange enums and constants

### 2. Infrastructure Layer - New Vnstock Adapters
- `app/infrastructure/data_sources/vnstock_adapter.py` - Main vnstock integration adapter
- `app/infrastructure/data_sources/vci_adapter.py` - VCI data source adapter
- `app/infrastructure/data_sources/tcbs_adapter.py` - TCBS data source adapter
- `app/infrastructure/data_sources/msn_adapter.py` - MSN data source adapter

### 3. Application Services
- `app/core/application/vietnamese_market_service.py` - Vietnamese market business logic
- `app/core/application/vnstock_data_service.py` - Vnstock data processing service

### 4. Agent Extensions
- `app/agents/search_agent.py` - Add Vietnamese market data sources
- `app/agents/analyze_agent.py` - Add Vietnamese financial analysis capabilities
- `app/agents/predict_agent.py` - Add Vietnamese market prediction models
- `app/agents/retriever_agent.py` - Add Vietnamese data retrieval capabilities

### 5. Database Migrations
- `scripts/migrations/005_vietnamese_market_data.sql` - Vietnamese market tables
- `scripts/migrations/006_vnstock_integration.sql` - Vnstock-specific data structures

### 6. Configuration and Dependencies
- `pyproject.toml` - Add vnstock dependency
- `config/settings.py` - Add Vietnamese market configuration
- `docker-compose.yml` - Add Vietnamese market data volume if needed

### 7. API Extensions
- `app/interfaces/api/v1/vietnamese_market_routes.py` - Vietnamese market API endpoints
- `app/interfaces/api/v1/__init__.py` - Register new routes

### 8. Tests
- `tests/unit/infrastructure/test_vnstock_adapters.py` - Vnstock adapter tests
- `tests/integration/test_vietnamese_market_integration.py` - Integration tests
- `tests/unit/agents/test_vietnamese_analysis_agent.py` - Agent extension tests

## Implementation Checklist

### Phase 1: Foundation Setup
- [ ] Add vnstock dependency to pyproject.toml
- [ ] Create Vietnamese market data models in domain layer
- [ ] Design vnstock adapter interfaces following hexagonal architecture
- [ ] Create database migration scripts for Vietnamese market data

### Phase 2: Data Source Integration
- [ ] Implement VCI data source adapter
- [ ] Implement TCBS data source adapter  
- [ ] Implement MSN data source adapter
- [ ] Create unified vnstock adapter that coordinates all sources
- [ ] Add error handling and rate limiting for Vietnamese data sources

### Phase 3: Agent Extensions
- [ ] Extend Search Agent to include Vietnamese market data sources
- [ ] Extend Analyze Agent with Vietnamese financial analysis capabilities
- [ ] Extend Retriever Agent to handle Vietnamese market queries
- [ ] Extend Predict Agent with Vietnamese market prediction models
- [ ] Update Guard Agent to validate Vietnamese market queries

### Phase 4: Business Logic Integration
- [ ] Create Vietnamese Market Service for business logic
- [ ] Create Vnstock Data Service for data processing
- [ ] Integrate Vietnamese market data into existing workflows
- [ ] Add Vietnamese market-specific financial calculations

### Phase 5: API and Interface Updates
- [ ] Create Vietnamese market API endpoints
- [ ] Update existing API responses to include Vietnamese data
- [ ] Add Vietnamese market query validation
- [ ] Create Vietnamese market data export capabilities

### Phase 6: Testing and Validation
- [ ] Create comprehensive unit tests for all new components
- [ ] Create integration tests for Vietnamese market workflows
- [ ] Create end-to-end tests for Vietnamese market analysis
- [ ] Performance testing for Vietnamese data retrieval
- [ ] Validate data accuracy and consistency

### Phase 7: Documentation and Deployment
- [ ] Update API documentation with Vietnamese market endpoints
- [ ] Create Vietnamese market usage examples
- [ ] Update system architecture documentation
- [ ] Create deployment guide for Vietnamese market features
- [ ] Add monitoring and logging for Vietnamese market operations

## Technical Implementation Details

### Data Model Extensions

```python
class VietnameseStock(StockData):
    exchange: VietnameseExchange
    market_cap: Optional[float]
    free_float: Optional[float]
    listing_date: Optional[datetime]
    sector: Optional[str]
    industry: Optional[str]

class VietnameseCompany(Company):
    vnstock_symbol: str
    exchange: VietnameseExchange
    industry_icb_code: Optional[str]
    market_cap: Optional[float]
    free_float: Optional[float]
    listing_date: Optional[datetime]
```

### Vnstock Adapter Architecture

```python
class VnstockAdapter(ABC):
    @abstractmethod
    async def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[StockData]
    
    @abstractmethod
    async def get_company_info(self, symbol: str) -> VietnameseCompany
    
    @abstractmethod
    async def get_financial_reports(self, symbol: str, period: str) -> List[FinancialReport]
```

### Agent Integration Points

- **Search Agent**: Add Vietnamese market data sources to external API searches
- **Analyze Agent**: Include Vietnamese financial metrics and ratios in analysis
- **Retriever Agent**: Add Vietnamese market data to vector database retrieval
- **Predict Agent**: Include Vietnamese market trends in predictions

## Risk Mitigation

1. **Data Source Reliability**: Implement fallback mechanisms between VCI, TCBS, and MSN
2. **Rate Limiting**: Add proper rate limiting for Vietnamese data sources
3. **Data Consistency**: Validate data consistency across different sources
4. **Performance**: Optimize Vietnamese data retrieval for large datasets
5. **Error Handling**: Robust error handling for Vietnamese market data failures

## Success Metrics

- [ ] Vietnamese market data retrieval success rate > 95%
- [ ] Vietnamese market analysis accuracy > 90%
- [ ] API response time for Vietnamese queries < 2 seconds
- [ ] Zero data inconsistencies between sources
- [ ] 100% test coverage for Vietnamese market components

## Additional Ideas (Not Implemented in This Phase)

- Real-time Vietnamese market data streaming
- Vietnamese market sentiment analysis using Vietnamese news sources
- Vietnamese market technical indicators and charting
- Vietnamese market portfolio optimization
- Vietnamese market risk assessment models
- Integration with Vietnamese regulatory data sources
- Vietnamese market compliance and reporting features
