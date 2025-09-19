# Vnstock Company Information Functions Implementation Plan

## Overview of Current State

The QuantyFinAI Agent system currently has:
- **Vietnamese Market Service**: Comprehensive service for Vietnamese market data operations
- **Data Source Adapters**: VCI, TCBS, MSN adapters implementing the VnstockAdapter interface
- **Domain Models**: Complete Vietnamese market models including VietnameseCompany, VietnameseNews, VietnameseEvent, VietnameseShareholder, etc.
- **Basic Company Functions**: Some company information functions already implemented in VCI adapter

## Overview of Final State

After implementing the Vnstock company information functions, the system will have:
- **Complete Company Information API**: All company information functions from Vnstock documentation
- **Enhanced Data Models**: Extended models for shareholders, officers, subsidiaries, events
- **Unified Company Service**: Comprehensive company information service with fallback support
- **Agent Integration**: All agents will have access to detailed company information
- **API Endpoints**: RESTful endpoints for all company information functions

## Files to Change

### 1. Domain Models Extensions (`app/core/domain/models.py`)
- Add `VietnameseOfficer` model for management and board members
- Add `VietnameseSubsidiary` model for subsidiary companies
- Add `VietnameseCorporateEvent` model for corporate events and announcements
- Extend `VietnameseShareholder` model with additional fields
- Add `VietnameseCompanyOverview` model for comprehensive company overview

### 2. VCI Adapter Extensions (`app/infrastructure/data_sources/vci_adapter.py`)
- Implement `get_company_overview()` - Basic company information
- Implement `get_company_shareholders()` - Major shareholders information
- Implement `get_company_officers()` - Management and board members
- Implement `get_company_subsidiaries()` - Subsidiary companies
- Implement `get_company_events()` - Corporate events and announcements
- Implement `get_company_financial_analysis()` - Financial analysis and ratios
- Implement `get_company_trading_statistics()` - Trading volume and statistics

### 3. TCBS Adapter Extensions (`app/infrastructure/data_sources/tcbs_adapter.py`)
- Implement all company information functions for TCBS data source
- Add fallback support for company information functions

### 4. MSN Adapter Extensions (`app/infrastructure/data_sources/msn_adapter.py`)
- Implement all company information functions for MSN data source
- Add fallback support for company information functions

### 5. Vietnamese Market Service Extensions (`app/core/application/vietnamese_market_service.py`)
- Add `get_company_overview()` method with fallback support
- Add `get_company_shareholders()` method with fallback support
- Add `get_company_officers()` method with fallback support
- Add `get_company_subsidiaries()` method with fallback support
- Add `get_company_events()` method with fallback support
- Add `get_company_financial_analysis()` method with fallback support
- Add `get_company_trading_statistics()` method with fallback support

### 6. API Routes (`app/interfaces/api/v1/`)
- Create `company_info_routes.py` with all company information endpoints
- Update `__init__.py` to register new routes

### 7. Database Migrations (`scripts/migrations/`)
- Create `006_company_info_tables.sql` for new company information tables
- Add indexes for performance optimization

### 8. Tests
- Create `test_company_info_functions.py` for unit tests
- Create `test_company_info_integration.py` for integration tests

## Implementation Checklist

### Phase 1: Domain Models and Database Schema
- [ ] Add `VietnameseOfficer` model with fields: id, vnstock_symbol, officer_name, position, ownership_percentage, shares_held, status, report_date
- [ ] Add `VietnameseSubsidiary` model with fields: id, vnstock_symbol, subsidiary_name, ownership_percentage, subsidiary_type, report_date
- [ ] Add `VietnameseCorporateEvent` model with fields: id, vnstock_symbol, event_type, title, description, event_date, record_date, ex_date, status
- [ ] Extend `VietnameseShareholder` model with additional fields: shareholder_id, shareholder_type, is_major_shareholder, report_date
- [ ] Add `VietnameseCompanyOverview` model for comprehensive company information
- [ ] Create database migration script for new tables
- [ ] Add database indexes for performance optimization

### Phase 2: VCI Adapter Company Information Functions
- [ ] Implement `get_company_overview()` using `company.overview()`
- [ ] Implement `get_company_shareholders()` using `company.shareholders()`
- [ ] Implement `get_company_officers()` using `company.officers(filter_by='all')`
- [ ] Implement `get_company_subsidiaries()` using `company.subsidiaries()`
- [ ] Implement `get_company_events()` using `company.events()`
- [ ] Implement `get_company_financial_analysis()` using `company.financial_analysis()`
- [ ] Implement `get_company_trading_statistics()` using `company.trading_statistics()`
- [ ] Add data conversion methods for each function
- [ ] Add error handling and validation for each function

### Phase 3: TCBS Adapter Company Information Functions
- [ ] Implement all company information functions for TCBS data source
- [ ] Add data conversion methods for TCBS-specific data formats
- [ ] Add error handling and validation for TCBS functions
- [ ] Test TCBS adapter functions

### Phase 4: MSN Adapter Company Information Functions
- [ ] Implement all company information functions for MSN data source
- [ ] Add data conversion methods for MSN-specific data formats
- [ ] Add error handling and validation for MSN functions
- [ ] Test MSN adapter functions

### Phase 5: Vietnamese Market Service Extensions
- [ ] Add `get_company_overview()` method with fallback support
- [ ] Add `get_company_shareholders()` method with fallback support
- [ ] Add `get_company_officers()` method with fallback support
- [ ] Add `get_company_subsidiaries()` method with fallback support
- [ ] Add `get_company_events()` method with fallback support
- [ ] Add `get_company_financial_analysis()` method with fallback support
- [ ] Add `get_company_trading_statistics()` method with fallback support
- [ ] Add caching support for company information functions
- [ ] Add rate limiting for company information functions

### Phase 6: API Endpoints
- [ ] Create `company_info_routes.py` with RESTful endpoints
- [ ] Add GET `/api/v1/company/{symbol}/overview` endpoint
- [ ] Add GET `/api/v1/company/{symbol}/shareholders` endpoint
- [ ] Add GET `/api/v1/company/{symbol}/officers` endpoint
- [ ] Add GET `/api/v1/company/{symbol}/subsidiaries` endpoint
- [ ] Add GET `/api/v1/company/{symbol}/events` endpoint
- [ ] Add GET `/api/v1/company/{symbol}/financial-analysis` endpoint
- [ ] Add GET `/api/v1/company/{symbol}/trading-statistics` endpoint
- [ ] Add query parameters for filtering and pagination
- [ ] Add response validation and error handling

### Phase 7: Agent Integration
- [ ] Update Search Agent to include company information in search results
- [ ] Update Analyze Agent to use company information for analysis
- [ ] Update Retriever Agent to retrieve company information from vector database
- [ ] Update Predict Agent to use company information for predictions
- [ ] Update Guard Agent to validate company information queries

### Phase 8: Testing and Validation
- [ ] Create unit tests for all company information functions
- [ ] Create integration tests for company information workflows
- [ ] Create end-to-end tests for company information API
- [ ] Test fallback mechanisms between data sources
- [ ] Test error handling and edge cases
- [ ] Performance testing for company information functions
- [ ] Validate data accuracy and consistency

### Phase 9: Documentation and Deployment
- [ ] Update API documentation with company information endpoints
- [ ] Create usage examples for company information functions
- [ ] Update system architecture documentation
- [ ] Create deployment guide for company information features
- [ ] Add monitoring and logging for company information operations

## Technical Implementation Details

### VCI Adapter Company Information Functions

```python
async def get_company_overview(self, symbol: str) -> Optional[VietnameseCompanyOverview]:
    """Get comprehensive company overview from VCI."""
    company_client = await self._get_company_client(symbol)
    overview_df = company_client.overview()
    return self._convert_overview_to_company_overview(overview_df, symbol)

async def get_company_shareholders(self, symbol: str) -> List[VietnameseShareholder]:
    """Get major shareholders from VCI."""
    company_client = await self._get_company_client(symbol)
    shareholders_df = company_client.shareholders()
    return self._convert_shareholders_to_vietnamese_shareholders(shareholders_df, symbol)

async def get_company_officers(self, symbol: str, filter_by: str = 'all') -> List[VietnameseOfficer]:
    """Get company officers from VCI."""
    company_client = await self._get_company_client(symbol)
    officers_df = company_client.officers(filter_by=filter_by)
    return self._convert_officers_to_vietnamese_officers(officers_df, symbol)
```

### Vietnamese Market Service Extensions

```python
async def get_company_overview(
    self,
    symbol: str,
    data_source: Optional[VnstockDataSource] = None,
) -> Optional[VietnameseCompanyOverview]:
    """Get company overview with fallback support."""
    data_source = data_source or self.config.default_data_source
    sources_to_try = [data_source] + (
        self.config.fallback_sources
        if self.config.enable_fallback
        else []
    )
    
    for source in sources_to_try:
        if source not in self._adapters:
            continue
            
        try:
            adapter = self._adapters[source]
            overview = await adapter.get_company_overview(symbol)
            if overview:
                return overview
        except Exception as e:
            self.logger.warning(f"Failed to fetch company overview from {source}: {e}")
    
    return None
```

### API Endpoints Structure

```python
@router.get("/company/{symbol}/overview")
async def get_company_overview(
    symbol: str,
    data_source: Optional[VnstockDataSource] = None,
    service: VietnameseMarketService = Depends(get_vietnamese_market_service)
) -> VietnameseCompanyOverview:
    """Get comprehensive company overview."""
    return await service.get_company_overview(symbol, data_source)

@router.get("/company/{symbol}/shareholders")
async def get_company_shareholders(
    symbol: str,
    limit: int = 10,
    data_source: Optional[VnstockDataSource] = None,
    service: VietnameseMarketService = Depends(get_vietnamese_market_service)
) -> List[VietnameseShareholder]:
    """Get major shareholders information."""
    return await service.get_company_shareholders(symbol, limit, data_source)
```

## Data Source Mapping

### VCI Data Source Functions
- `company.overview()` → `get_company_overview()`
- `company.shareholders()` → `get_company_shareholders()`
- `company.officers(filter_by='all')` → `get_company_officers()`
- `company.subsidiaries()` → `get_company_subsidiaries()`
- `company.events()` → `get_company_events()`
- `company.news()` → `get_company_news()` (already implemented)
- `company.financial_analysis()` → `get_company_financial_analysis()`
- `company.trading_statistics()` → `get_company_trading_statistics()`

### TCBS Data Source Functions
- Similar mapping for TCBS-specific company information functions
- Fallback support when VCI is unavailable

### MSN Data Source Functions
- Similar mapping for MSN-specific company information functions
- Fallback support when VCI and TCBS are unavailable

## Error Handling and Validation

- **Symbol Validation**: Ensure valid Vietnamese stock symbols
- **Data Source Fallback**: Automatic fallback between VCI, TCBS, and MSN
- **Rate Limiting**: Respect API rate limits for each data source
- **Data Validation**: Validate data structure and content
- **Error Logging**: Comprehensive logging for debugging and monitoring
- **Timeout Handling**: Proper timeout handling for external API calls

## Performance Optimization

- **Caching**: Cache company information for frequently accessed symbols
- **Parallel Requests**: Fetch multiple company information types in parallel
- **Data Pagination**: Implement pagination for large datasets
- **Database Indexing**: Optimize database queries with proper indexes
- **Response Compression**: Compress API responses for better performance

## Security Considerations

- **Input Validation**: Validate all input parameters
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Data Sanitization**: Sanitize data before storing in database
- **Access Control**: Implement proper access control for sensitive company information
- **Audit Logging**: Log all company information access for security auditing

## Success Metrics

- [ ] Company information retrieval success rate > 95%
- [ ] API response time for company information < 2 seconds
- [ ] Data accuracy and consistency across all sources
- [ ] 100% test coverage for company information functions
- [ ] Zero data inconsistencies between sources
- [ ] Successful fallback mechanism operation

## Additional Ideas (Not Implemented in This Phase)

- Real-time company information updates via WebSocket
- Company information change notifications
- Advanced company information analytics and insights
- Company information export to various formats (PDF, Excel, CSV)
- Company information comparison tools
- Historical company information tracking
- Company information sentiment analysis
- Integration with Vietnamese regulatory data sources
