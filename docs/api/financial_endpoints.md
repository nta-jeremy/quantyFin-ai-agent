# Financial Reporting API Documentation

## Overview

The Financial Reporting API provides comprehensive access to Vietnamese stock market financial data including balance sheets, income statements, cash flow statements, and financial ratios. The API supports multiple data sources (VCI, TCBS) with intelligent caching and fallback mechanisms.

## Base URL

```
http://localhost:8000/api/v1/financial
```

## Authentication

All financial endpoints require authentication:
- **Bearer Token**: Include `Authorization: Bearer <token>` header
- **API Key**: Include `X-API-Key: <key>` header
- **Rate Limiting**: 100 requests per minute per user

## Data Sources

| Source | Description | Language Support | Coverage |
|--------|-------------|------------------|----------|
| VCI | Vietnam Credit Information Agency | Vietnamese, English | Comprehensive |
| TCBS | TP Securities | Vietnamese, English | Major stocks |

## Common Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `symbol` | string | Yes | - | Stock symbol (e.g., "ACB", "VCB") |
| `source` | enum | No | "VCI" | Data source: "VCI" or "TCBS" |
| `period` | string | No | "year" | Report period: "year" or "quarter" |
| `language` | string | No | "vi" | Language: "vi" or "en" |
| `use_cache` | boolean | No | true | Use cached data if available |

## Response Format

All endpoints return a standardized response format:

```json
{
  "success": true,
  "data": { /* Financial data */ },
  "timestamp": "2023-12-31T10:30:00.000Z"
}
```

## Endpoints

### 1. Balance Sheet

**GET** `/balance-sheet/{symbol}`

Retrieve balance sheet data including assets, liabilities, and equity information.

**Response Data Structure:**
```json
{
  "data": {
    "data": [
      {
        "period_end": "2023-12-31T00:00:00",
        "symbol": "ACB",
        "source": "VCI",
        "language": "vi",
        "total_assets": 1000000000,
        "current_assets": 600000000,
        "cash_and_equivalents": 100000000,
        "non_current_assets": 400000000,
        "total_liabilities": 500000000,
        "current_liabilities": 300000000,
        "non_current_liabilities": 200000000,
        "total_equity": 500000000
      }
    ],
    "metadata": {
      "source": "VCI",
      "from_cache": false,
      "retrieved_at": "2023-12-31T10:30:00.000Z",
      "processing_time_ms": 150,
      "record_count": 1
    }
  }
}
```

**CURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/financial/balance-sheet/ACB?source=VCI&period=year&language=vi" \
  -H "Authorization: Bearer <token>"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/api/v1/financial/balance-sheet/ACB"
headers = {"Authorization": "Bearer <token>"}
params = {
    "source": "VCI",
    "period": "year",
    "language": "vi",
    "use_cache": True
}

response = requests.get(url, headers=headers, params=params)
data = response.json()
```

### 2. Income Statement

**GET** `/income-statement/{symbol}`

Retrieve income statement data including revenue, expenses, and profitability metrics.

**Key Fields:**
- `total_revenue`: Total operating revenue
- `cost_of_goods_sold`: Cost of goods and services sold
- `gross_profit`: Gross profit (revenue - COGS)
- `operating_income`: Income from core operations
- `net_income`: Net income after all expenses
- `eps`: Earnings per share

**Response Structure:** Similar to balance sheet with income-specific fields.

### 3. Cash Flow Statement

**GET** `/cash-flow/{symbol}`

Retrieve cash flow statement data showing cash movements across operating, investing, and financing activities.

**Key Fields:**
- `operating_cash_flow`: Cash from core business operations
- `investing_cash_flow`: Cash from investment activities
- `financing_cash_flow`: Cash from financing activities
- `net_cash_flow`: Net change in cash position
- `cash_beginning_period`: Cash at start of period
- `cash_end_period`: Cash at end of period

### 4. Financial Ratios

**GET** `/financial-ratios/{symbol}`

Retrieve financial ratios and metrics for fundamental analysis.

**Ratio Categories:**

**Valuation Ratios:**
- `pe_ratio`: Price-to-earnings ratio
- `pb_ratio`: Price-to-book ratio
- `ps_ratio`: Price-to-sales ratio
- `ev_ebitda`: Enterprise value to EBITDA

**Profitability Ratios:**
- `roe`: Return on equity
- `roa`: Return on assets
- `gross_margin`: Gross profit margin
- `operating_margin`: Operating profit margin
- `net_margin`: Net profit margin

**Liquidity Ratios:**
- `current_ratio`: Current assets / current liabilities
- `quick_ratio`: (Current assets - inventory) / current liabilities
- `cash_ratio`: Cash / current liabilities

**Leverage Ratios:**
- `debt_to_equity`: Total debt / total equity
- `debt_to_assets`: Total debt / total assets
- `interest_coverage`: EBIT / interest expense

**Efficiency Ratios:**
- `asset_turnover`: Revenue / total assets
- `inventory_turnover`: COGS / average inventory
- `receivables_turnover`: Revenue / average receivables

### 5. Comprehensive Financial Data

**GET** `/comprehensive/{symbol}`

Retrieve all financial data types in a single concurrent request.

**Response Structure:**
```json
{
  "data": {
    "balance_sheet": { /* Balance sheet data */ },
    "income_statement": { /* Income statement data */ },
    "cash_flow": { /* Cash flow data */ },
    "financial_ratios": { /* Financial ratios data */ },
    "metadata": {
      "processing_time_ms": 350,
      "data_sources": ["VCI"],
      "cache_status": {
        "balance_sheet": true,
        "income_statement": true,
        "cash_flow": false,
        "financial_ratios": true
      }
    }
  }
}
```

**Performance Note:** This endpoint makes concurrent requests to all data sources and typically completes in 300-500ms.

### 6. Cache Management

**DELETE** `/cache`

Clear cached financial reports data.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | No | Specific symbol to clear |
| `report_type` | string | No | Report type to clear |
| `source` | string | No | Data source to clear |

**Response:**
```json
{
  "success": true,
  "message": "Cache cleared successfully",
  "keys_removed": 5,
  "bytes_freed": 10240,
  "timestamp": "2023-12-31T10:30:00.000Z"
}
```

**Examples:**
```bash
# Clear all cache
curl -X DELETE "http://localhost:8000/api/v1/financial/cache" \
  -H "Authorization: Bearer <token>"

# Clear cache for specific symbol
curl -X DELETE "http://localhost:8000/api/v1/financial/cache?symbol=ACB" \
  -H "Authorization: Bearer <token>"

# Clear balance sheet cache
curl -X DELETE "http://localhost:8000/api/v1/financial/cache?report_type=balance_sheet" \
  -H "Authorization: Bearer <token>"
```

### 7. Service Metrics

**GET** `/metrics`

Retrieve performance metrics for the financial reports service.

**Response:**
```json
{
  "success": true,
  "data": {
    "cache": {
      "hit_rate": 0.85,
      "total_keys": 150,
      "memory_usage_bytes": 2048576,
      "avg_response_time_ms": 45
    },
    "service_health": {
      "status": "healthy",
      "uptime_seconds": 86400,
      "last_health_check": "2023-12-31T10:30:00.000Z"
    },
    "performance": {
      "avg_response_time_ms": 120,
      "p95_response_time_ms": 350,
      "error_rate": 0.02,
      "requests_per_minute": 50
    },
    "data_sources": {
      "VCI": {
        "availability": 0.98,
        "avg_response_time_ms": 180,
        "last_success": "2023-12-31T10:29:00.000Z"
      },
      "TCBS": {
        "availability": 0.95,
        "avg_response_time_ms": 220,
        "last_success": "2023-12-31T10:28:00.000Z"
      }
    }
  }
}
```

## Error Handling

The API uses standard HTTP status codes:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (invalid/missing authentication) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found (symbol not found) |
| 422 | Unprocessable Entity (validation error) |
| 429 | Too Many Requests (rate limit exceeded) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (data source unavailable) |

**Error Response Format:**
```json
{
  "detail": "Symbol ACB not found in data source VCI"
}
```

## Caching Strategy

### Cache TTL (Time-to-Live)
- **Balance Sheet**: 4 hours
- **Income Statement**: 4 hours
- **Cash Flow**: 4 hours
- **Financial Ratios**: 4 hours
- **Comprehensive**: 4 hours

### Cache Keys
Cache keys are generated based on:
- Symbol
- Data source
- Report type
- Period (year/quarter)
- Language

### Cache Invalidation
- Automatic TTL expiration
- Manual clearing via DELETE /cache endpoint
- Stale-while-revalidate strategy for continued availability

## Rate Limiting

- **Default**: 100 requests per minute per user
- **Burst**: 10 requests per second
- **Headers included in response**:
  - `X-RateLimit-Limit`: Requests allowed per window
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

## Best Practices

### 1. Cache Usage
- Always use `use_cache=true` for better performance
- Use `use_cache=false` only when fresh data is required
- Clear cache symbol-specifically when needed rather than clearing all

### 2. Error Handling
- Implement retry logic for 503 errors with exponential backoff
- Handle 404 errors gracefully (symbol not found)
- Monitor rate limiting headers to avoid throttling

### 3. Performance Optimization
- Use comprehensive endpoint when multiple report types are needed
- Prefer yearly data over quarterly for historical analysis
- Implement client-side caching for frequently accessed symbols

### 4. Data Validation
- Validate symbol format before making requests
- Check response data completeness before processing
- Handle missing fields gracefully with default values

## Integration Examples

### JavaScript/TypeScript
```typescript
interface FinancialData {
  symbol: string;
  balanceSheet: BalanceSheetData[];
  incomeStatement: IncomeStatementData[];
  cashFlow: CashFlowData[];
  ratios: FinancialRatioData[];
}

async function getFinancialData(symbol: string): Promise<FinancialData> {
  const response = await fetch(`/api/v1/financial/comprehensive/${symbol}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}
```

### Python with Async
```python
import aiohttp
import asyncio

async def fetch_financial_data(session, symbol, token):
    url = f"http://localhost:8000/api/v1/financial/comprehensive/{symbol}"
    headers = {"Authorization": f"Bearer {token}"}

    async with session.get(url, headers=headers) as response:
        return await response.json()

async def main():
    symbols = ["ACB", "VCB", "TCB"]
    token = "your-api-token"

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_financial_data(session, sym, token) for sym in symbols]
        results = await asyncio.gather(*tasks)

        for symbol, data in zip(symbols, results):
            print(f"{symbol}: {len(data['data']['balance_sheet']['data'])} records")
```

## Troubleshooting

### Common Issues

**1. Authentication Errors**
- Verify token is valid and not expired
- Check Authorization header format
- Ensure user has required permissions

**2. Rate Limiting**
- Monitor X-RateLimit headers
- Implement backoff logic
- Consider batch requests for multiple symbols

**3. Slow Response Times**
- Enable caching with `use_cache=true`
- Use comprehensive endpoint for multiple data types
- Check network latency and data source availability

**4. Data Quality Issues**
- Verify symbol exists in data source
- Check data source coverage for requested symbol
- Use fallback data source when primary is unavailable

### Debug Headers

Add these headers for debugging:
```
X-Debug: true          # Enable debug information in responses
X-Cache-Debug: true    # Include cache debugging info
X-Trace-ID: uuid        # Track requests across services
```

## Support

For API support and issues:
- Create GitHub issue with detailed reproduction steps
- Include request ID from response headers
- Provide error timestamps and symbols affected
- Include expected vs actual behavior

## Changelog

### v1.0.0 (2023-12-31)
- Initial release with financial reporting endpoints
- Support for VCI and TCBS data sources
- Comprehensive caching and fallback mechanisms
- Bilingual support (Vietnamese/English)
- Performance optimization with concurrent requests