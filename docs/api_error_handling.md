# API Error Handling Documentation

## Overview

This document provides comprehensive information about error handling in the Vnstock Historical Data API, including common errors, their causes, and recommended solutions.

## Error Response Format

All API errors follow a consistent JSON format:

```json
{
  "detail": "Error message describing the issue",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

## Common Error Types

### 1. Authentication Errors (401)

**Status Code:** `401 Unauthorized`

**Description:** Authentication is required or has failed.

**Common Causes:**
- Missing or invalid JWT token
- Expired token
- Invalid API key

**Example Response:**
```json
{
  "detail": "Authentication required: Invalid or missing JWT token",
  "error_code": "AUTH_REQUIRED",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

**Solution:**
- Ensure you have a valid JWT token
- Include the token in the Authorization header: `Authorization: Bearer YOUR_TOKEN`
- Refresh expired tokens using the refresh endpoint

### 2. Authorization Errors (403)

**Status Code:** `403 Forbidden`

**Description:** User lacks permission to access the requested resource.

**Common Causes:**
- Insufficient user role/permissions
- API key lacks required scopes
- Rate limit exceeded

**Example Response:**
```json
{
  "detail": "Insufficient permissions: User role 'viewer' cannot access this endpoint",
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

**Solution:**
- Verify user has appropriate permissions
- Check API key scopes
- Wait if rate limited (check `Retry-After` header)

### 3. Not Found Errors (404)

**Status Code:** `404 Not Found`

**Description:** Requested resource does not exist.

**Common Causes:**
- Invalid asset symbol
- Asset not available in requested data source
- Endpoint not found

**Example Response:**
```json
{
  "detail": "Symbol 'INVALID_SYMBOL' not found in data source 'VCI'",
  "error_code": "SYMBOL_NOT_FOUND",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

**Solution:**
- Verify the symbol is correct
- Check if the asset is available in the specified data source
- Try an alternative data source

### 4. Validation Errors (400)

**Status Code:** `400 Bad Request`

**Description:** Request parameters are invalid or malformed.

**Common Causes:**
- Invalid date format
- Invalid time interval
- Missing required parameters
- Date range validation failed

**Example Response:**
```json
{
  "detail": "Invalid date format: '2024-13-01'. Expected YYYY-MM-DD format",
  "error_code": "INVALID_DATE_FORMAT",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

**Solution:**
- Verify all parameters are correctly formatted
- Check date format (YYYY-MM-DD)
- Ensure start_date is before end_date
- Validate time interval is supported

### 5. Rate Limiting Errors (429)

**Status Code:** `429 Too Many Requests`

**Description:** API rate limit has been exceeded.

**Common Causes:**
- Too many requests in a short time period
- Exceeded per-minute or per-hour limits
- Concurrent request limit exceeded

**Example Response:**
```json
{
  "detail": "Rate limit exceeded: 100 requests per minute per user",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

**Headers:**
- `Retry-After`: Number of seconds to wait before retrying
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when window resets

**Solution:**
- Implement backoff retry logic
- Check Retry-After header
- Consider caching responses
- Use bulk endpoints for multiple symbols

### 6. Service Unavailable Errors (503)

**Status Code:** `503 Service Unavailable`

**Description:** Data source is temporarily unavailable.

**Common Causes:**
- Data source API is down
- Network connectivity issues
- Data source maintenance

**Example Response:**
```json
{
  "detail": "Data source 'VCI' is currently unavailable. Please try again later.",
  "error_code": "DATA_SOURCE_UNAVAILABLE",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

**Solution:**
- Retry the request after a delay
- Use fallback data sources if available
- Check data source status endpoints

### 7. Gateway Timeout Errors (504)

**Status Code:** `504 Gateway Timeout`

**Description:** Request to data source timed out.

**Common Causes:**
- Data source response too slow
- Large data requests
- Network congestion

**Example Response:**
```json
{
  "detail": "Request timeout: Data source did not respond within 30 seconds",
  "error_code": "REQUEST_TIMEOUT",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

**Solution:**
- Reduce the date range for requests
- Use larger time intervals
- Implement retry logic with exponential backoff
- Check network connectivity

### 8. Internal Server Errors (500)

**Status Code:** `500 Internal Server Error`

**Description:** Unexpected server error occurred.

**Common Causes:**
- Server-side bug or exception
- Database connection issues
- Cache server problems

**Example Response:**
```json
{
  "detail": "Internal server error: Unexpected error processing request",
  "error_code": "INTERNAL_SERVER_ERROR",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

**Solution:**
- Retry the request
- Check API status page
- Contact support with request_id

## Error Recovery Strategies

### 1. Retry Logic

Implement exponential backoff for retryable errors:

```python
import time
import random

def retry_request(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
```

### 2. Fallback Data Sources

When primary data source fails, try alternatives:

```python
data_sources = ["VCI", "TCBS", "MSN"]
for source in data_sources:
    try:
        response = requests.get(
            f"{BASE_URL}/historical/data?symbol=VNM&data_source={source}",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
    except:
        continue
```

### 3. Cache Utilization

Use caching to reduce API calls and improve performance:

```python
# Enable caching
response = requests.get(
    f"{BASE_URL}/historical/data?symbol=VNM&use_cache=true",
    headers=headers
)
```

## Rate Limiting

### Current Limits
- **Standard Users:** 100 requests per minute
- **Premium Users:** 500 requests per minute
- **Enterprise Users:** 2000 requests per minute

### Best Practices
1. Implement client-side rate limiting
2. Use bulk endpoints for multiple symbols
3. Cache responses when appropriate
4. Monitor remaining requests with headers

## Data Source Health Monitoring

Check data source availability before making requests:

```bash
curl -X GET "https://api.quantyfin.ai/api/v1/historical/data/sources/health" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
[
  {
    "source": "VCI",
    "is_available": true,
    "last_checked": "2024-01-01T12:00:00Z",
    "response_time_ms": 150.5,
    "error_message": null
  },
  {
    "source": "TCBS",
    "is_available": false,
    "last_checked": "2024-01-01T12:00:00Z",
    "response_time_ms": null,
    "error_message": "Connection timeout"
  }
]
```

## Error Monitoring and Logging

### Request ID Tracking
Always include the request ID when reporting issues:

```bash
curl -X GET "https://api.quantyfin.ai/api/v1/historical/data?symbol=VNM" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "X-Request-ID: unique-request-id"
```

### Logging Recommendations
1. Log all API responses and errors
2. Include request_id in logs
3. Monitor error rates and response times
4. Set up alerts for critical errors

## Common Error Scenarios and Solutions

### Scenario 1: Invalid Symbol
**Error:** `404 Symbol not found`
**Solution:**
- Verify symbol exists in the target market
- Check symbol spelling and case sensitivity
- Try alternative data sources

### Scenario 2: Date Range Too Large
**Error:** `400 Invalid date range`
**Solution:**
- Reduce date range to maximum 10 years
- Use larger time intervals for historical data
- Split requests into smaller date ranges

### Scenario 3: Rate Limit Exceeded
**Error:** `429 Rate limit exceeded`
**Solution:**
- Implement backoff retry logic
- Use bulk endpoints for multiple symbols
- Consider upgrading your plan for higher limits

### Scenario 4: Data Source Unavailable
**Error:** `503 Data source unavailable`
**Solution:**
- Retry after delay
- Use fallback data sources
- Check data source status endpoint

### Scenario 5: Authentication Issues
**Error:** `401 Authentication required`
**Solution:**
- Verify JWT token is valid and not expired
- Check token is included in Authorization header
- Refresh token if expired

## Support and Troubleshooting

### Getting Help
1. **Documentation:** Check API documentation first
2. **Status Page:** Monitor system status
3. **Error Codes:** Refer to this document for error-specific guidance
4. **Support:** Contact support with request_id and error details

### Reporting Issues
When reporting issues, include:
- Request ID from error response
- Full error message and status code
- Request parameters and headers
- Timestamp of the error
- Steps to reproduce the issue

### Debug Mode
For development, you can enable debug mode:

```bash
curl -X GET "https://api.quantyfin.ai/api/v1/historical/data?symbol=VNM&debug=true" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

This will include additional debugging information in error responses.

## Best Practices

### 1. Input Validation
- Validate all parameters before making requests
- Use appropriate data types and formats
- Sanitize user inputs

### 2. Error Handling
- Implement comprehensive error handling
- Use appropriate HTTP status codes
- Provide meaningful error messages

### 3. Retry Logic
- Implement exponential backoff for retryable errors
- Don't retry non-retryable errors (4xx)
- Use jitter to avoid thundering herd

### 4. Monitoring
- Monitor error rates and response times
- Set up alerts for critical errors
- Track API usage and limits

### 5. Performance
- Use caching for frequently accessed data
- Implement client-side rate limiting
- Use bulk endpoints for multiple symbols

This comprehensive error handling documentation will help developers integrate with the API more effectively and handle errors gracefully.