# API Reference

This document provides comprehensive API reference for the TSE Analysis System.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

Currently, no authentication is required for API access.

## Endpoints

### Market Data

#### GET /symbols

Get all available stock symbols.

**Response:**
```json
{
  "symbols": [
    {
      "id": "string",
      "name": "string",
      "market": "string"
    }
  ]
}
```

#### GET /symbols/{symbol_id}

Get detailed information for a specific symbol.

**Parameters:**
- `symbol_id` (path): Symbol identifier

**Response:**
```json
{
  "symbol": {
    "id": "string",
    "name": "string",
    "market": "string",
    "last_price": "number",
    "volume": "number"
  }
}
```

### Technical Analysis

#### GET /analysis/{symbol_id}

Get technical analysis for a symbol.

**Parameters:**
- `symbol_id` (path): Symbol identifier

**Response:**
```json
{
  "analysis": {
    "rsi": "number",
    "macd": "object",
    "bollinger_bands": "object",
    "prediction": "number"
  }
}
```

### System Status

#### GET /status

Get system status and health information.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "number",
  "database": "connected"
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

Error response format:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

## Rate Limiting

API requests are limited to 100 requests per minute per IP address.