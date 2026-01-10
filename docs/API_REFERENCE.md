# API Reference

Complete reference for the Self-Critique Planning Platform REST API and WebSocket endpoints.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Domains API](#domains-api)
6. [Planning API](#planning-api)
7. [Chat API](#chat-api)
8. [Validation API](#validation-api)
9. [Analytics API](#analytics-api)
10. [API Keys API](#api-keys-api)
11. [WebSocket Endpoints](#websocket-endpoints)

---

## Overview

### Base URL

```
Development: http://localhost:8000
Production: https://api.your-domain.com
```

### Content Type

All requests and responses use JSON:
```
Content-Type: application/json
```

### API Versioning

The API is versioned via URL path:
```
/api/v1/...
```

### Interactive Documentation

When the server is running, access interactive docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Authentication

### API Key Authentication

Include your API key in the `X-API-Key` header:

```bash
curl -X GET "http://localhost:8000/api/v1/domains" \
  -H "X-API-Key: sk_your-api-key-here"
```

### Getting an API Key

See [API Keys API](#api-keys-api) for creating and managing API keys.

---

## Rate Limiting

### Default Limits

| Endpoint Type | Limit |
|--------------|-------|
| Default (no API key) | 60 requests/minute |
| With API key | Configurable (default: 100/minute) |

### Rate Limit Headers

Every response includes rate limit information:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Your rate limit |
| `X-RateLimit-Remaining` | Requests remaining |
| `X-RateLimit-Reset` | Seconds until reset |

### Rate Limit Exceeded

When rate limited, you'll receive:

```json
{
  "detail": {
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "retry_after": 45
  }
}
```

**Status Code**: `429 Too Many Requests`

---

## Error Handling

### Error Response Format

```json
{
  "detail": {
    "error": "error_code",
    "message": "Human-readable description",
    "field": "optional_field_name"
  }
}
```

### Common Error Codes

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | `validation_error` | Invalid request data |
| 401 | `invalid_api_key` | Missing or invalid API key |
| 404 | `not_found` | Resource doesn't exist |
| 409 | `conflict` | Resource already exists |
| 422 | `unprocessable_entity` | Validation failed |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Server error |

---

## Domains API

Manage planning domains.

### Create Domain

Create a new planning domain.

```
POST /api/v1/domains
```

**Request Body:**
```json
{
  "name": "Kitchen Renovation",
  "description": "Planning domain for kitchen renovation project",
  "workspace_id": "00000000-0000-0000-0000-000000000001"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "00000000-0000-0000-0000-000000000001",
  "name": "Kitchen Renovation",
  "description": "Planning domain for kitchen renovation project",
  "domain_pddl": null,
  "problem_pddl": null,
  "is_public": false,
  "is_template": false,
  "created_at": "2026-01-06T10:30:00Z",
  "updated_at": "2026-01-06T10:30:00Z"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/domains" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"name": "Kitchen Renovation", "description": "Planning for kitchen project"}'
```

---

### List Domains

Get all domains.

```
GET /api/v1/domains
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip |
| `limit` | integer | 100 | Maximum records to return |
| `user_id` | UUID | - | Filter by user ID |

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Kitchen Renovation",
    "description": "Planning domain for kitchen renovation project",
    "status": "draft",
    "created_at": "2026-01-06T10:30:00Z",
    "updated_at": "2026-01-06T10:30:00Z"
  }
]
```

---

### Get Domain

Get a specific domain by ID.

```
GET /api/v1/domains/{domain_id}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `domain_id` | UUID | Domain identifier |

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "00000000-0000-0000-0000-000000000001",
  "name": "Kitchen Renovation",
  "description": "Planning domain for kitchen renovation project",
  "domain_pddl": "(define (domain kitchen) ...)",
  "problem_pddl": "(define (problem kitchen-reno) ...)",
  "is_public": false,
  "is_template": false,
  "created_at": "2026-01-06T10:30:00Z",
  "updated_at": "2026-01-06T11:45:00Z"
}
```

**Errors:**
- `404 Not Found`: Domain doesn't exist

---

### Update Domain

Update an existing domain.

```
PUT /api/v1/domains/{domain_id}
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "pddl_domain": "(define (domain ...) ...)",
  "pddl_problem": "(define (problem ...) ...)"
}
```

All fields are optional. Only provided fields are updated.

**Response:** `200 OK`

---

### Delete Domain

Delete a domain.

```
DELETE /api/v1/domains/{domain_id}
```

**Response:** `200 OK`
```json
{
  "message": "Domain deleted successfully"
}
```

---

## Planning API

Generate and manage plans.

### Create Planning Session

Start a new planning session.

```
POST /api/v1/planning/sessions
```

**Request Body:**
```json
{
  "domain_id": "550e8400-e29b-41d4-a716-446655440000",
  "problem": "Initial state: cabinets_old. Goal: cabinets_new, floor_new.",
  "max_iterations": 5,
  "model": "claude"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `domain_id` | UUID | Yes | - | Domain to plan for |
| `problem` | string | Yes | - | Problem description |
| `max_iterations` | integer | No | 5 | Max critique iterations |
| `model` | string | No | "claude" | LLM to use |

**Response:** `200 OK`
```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "domain_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-01-06T10:30:00Z"
}
```

---

### Get Planning Session

Get session details and results.

```
GET /api/v1/planning/sessions/{session_id}
```

**Response:** `200 OK`
```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "domain_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "current_iteration": 3,
  "max_iterations": 5,
  "plan": {
    "steps": [
      {"action": "remove_old_cabinets", "preconditions": [], "effects": ["cabinets_removed"]},
      {"action": "install_new_floor", "preconditions": ["cabinets_removed"], "effects": ["floor_new"]},
      {"action": "install_new_cabinets", "preconditions": ["floor_new"], "effects": ["cabinets_new"]}
    ],
    "is_valid": true
  },
  "iterations": [
    {
      "iteration": 1,
      "plan_version": "...",
      "critiques": [
        {"critic": "completeness", "feedback": "All goals achievable", "vote": "approve"},
        {"critic": "efficiency", "feedback": "Could parallelize steps 2-3", "vote": "suggest"},
        {"critic": "safety", "feedback": "No issues found", "vote": "approve"}
      ],
      "aggregated_score": 0.85
    }
  ],
  "created_at": "2026-01-06T10:30:00Z",
  "completed_at": "2026-01-06T10:32:00Z"
}
```

---

### List Planning Sessions

Get all sessions for a domain.

```
GET /api/v1/planning/sessions
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `domain_id` | UUID | Filter by domain |
| `status` | string | Filter by status |
| `limit` | integer | Max results (default: 50) |

---

## Chat API

Elicitation chat for domain definition. Chat sessions guide users through defining their planning domain and automatically generate PDDL when complete.

### Start Session

Start a new elicitation chat session, optionally linked to a domain.

```
POST /api/v1/chat/start
```

**Request Body:**
```json
{
  "domain_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain_id` | string | No | Domain to link this session to. If provided, generated PDDL will be saved to this domain. |

**Response:** `200 OK`
```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "phase": "intro",
  "domain_name": null,
  "domain_id": "550e8400-e29b-41d4-a716-446655440000",
  "completion_percentage": 0.0,
  "is_complete": false,
  "messages": [],
  "elicitation_state": {
    "phase": "intro",
    "domain_name": null,
    "objects": [],
    "predicates": [],
    "actions": [],
    "initial_state": [],
    "goal_state": []
  }
}
```

---

### Send Message

Send a message in an elicitation session and receive AI response.

```
POST /api/v1/chat/message
```

**Request Body:**
```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "I want to plan a software release process"
}
```

**Response:** `200 OK`
```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "I can help you plan a software release process. What are the main activities involved in your release workflow?",
  "phase": "objects",
  "completion_percentage": 15.0,
  "is_complete": false,
  "domain_pddl": null,
  "problem_pddl": null
}
```

**Note:** When the elicitation phase reaches "complete", `domain_pddl` and `problem_pddl` will contain the generated PDDL, which is also automatically saved to the linked domain.

---

### Get Session

Get session information including message history.

```
GET /api/v1/chat/session/{session_id}
```

**Response:** `200 OK`
```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "phase": "objects",
  "domain_name": "Software Release",
  "domain_id": "550e8400-e29b-41d4-a716-446655440000",
  "completion_percentage": 25.0,
  "is_complete": false,
  "messages": [
    {
      "role": "user",
      "content": "I want to plan a software release process",
      "timestamp": "2026-01-06T10:29:00Z"
    },
    {
      "role": "assistant",
      "content": "I can help with that...",
      "timestamp": "2026-01-06T10:29:05Z"
    }
  ],
  "elicitation_state": {
    "phase": "objects",
    "domain_name": "Software Release",
    "objects": ["code", "tests", "deployment"],
    "predicates": [],
    "actions": [],
    "initial_state": [],
    "goal_state": []
  }
}
```

**Note:** Messages persist in the session and are returned when retrieving the session, enabling chat history to survive page navigation.

---

### Delete Session

Delete an elicitation session.

```
DELETE /api/v1/chat/session/{session_id}
```

**Response:** `200 OK`
```json
{
  "status": "deleted"
}
```

---

### Generate PDDL

Manually trigger PDDL generation for a session. Useful when you want to generate PDDL before the elicitation is complete.

```
POST /api/v1/chat/session/{session_id}/generate-pddl
```

**Response:** `200 OK`
```json
{
  "domain_pddl": "(define (domain software-release) ...)",
  "problem_pddl": "(define (problem release-v1) ...)",
  "saved_to_domain": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `domain_pddl` | string | Generated PDDL domain definition |
| `problem_pddl` | string | Generated PDDL problem definition |
| `saved_to_domain` | boolean | Whether PDDL was saved to the linked domain |

---

## Validation API

Validate PDDL specifications.

### Validate Domain

Validate a PDDL domain specification.

```
POST /api/v1/validation/domain
```

**Request Body:**
```json
{
  "pddl": "(define (domain kitchen)\n  (:requirements :strips)\n  (:predicates (cabinet-installed) (floor-installed))\n  (:action install-cabinet\n    :precondition (floor-installed)\n    :effect (cabinet-installed)))"
}
```

**Response:** `200 OK`
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    {
      "type": "unused_predicate",
      "message": "Predicate 'floor-installed' is never produced by any action",
      "location": {"line": 4, "column": 15}
    }
  ],
  "parsed": {
    "name": "kitchen",
    "requirements": ["strips"],
    "predicates": ["cabinet-installed", "floor-installed"],
    "actions": ["install-cabinet"]
  }
}
```

---

### Validate Problem

Validate a PDDL problem specification.

```
POST /api/v1/validation/problem
```

**Request Body:**
```json
{
  "pddl": "(define (problem kitchen-reno)\n  (:domain kitchen)\n  (:init (floor-installed))\n  (:goal (cabinet-installed)))"
}
```

---

### Validate Complete

Validate domain and problem together.

```
POST /api/v1/validation/complete
```

**Request Body:**
```json
{
  "domain_pddl": "(define (domain ...) ...)",
  "problem_pddl": "(define (problem ...) ...)"
}
```

---

## Analytics API

Usage statistics and analytics.

### Get Usage Summary

Get aggregated usage statistics.

```
GET /api/v1/analytics/summary
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | UUID | - | Filter by user |
| `days` | integer | 30 | Number of days |

**Response:** `200 OK`
```json
{
  "total_requests": 1250,
  "successful_requests": 1180,
  "failed_requests": 70,
  "avg_latency_ms": 245.5,
  "total_llm_tokens": 150000,
  "planning_sessions": 45
}
```

---

### Get Endpoint Statistics

Get per-endpoint statistics.

```
GET /api/v1/analytics/endpoints
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | UUID | - | Filter by user |
| `days` | integer | 30 | Number of days |
| `limit` | integer | 10 | Number of endpoints |

**Response:** `200 OK`
```json
[
  {
    "endpoint": "/api/v1/planning/sessions",
    "request_count": 450,
    "avg_latency_ms": 1250.5,
    "error_rate": 2.5
  },
  {
    "endpoint": "/api/v1/domains",
    "request_count": 380,
    "avg_latency_ms": 85.2,
    "error_rate": 0.5
  }
]
```

---

### Get Daily Usage

Get daily usage trends.

```
GET /api/v1/analytics/daily
```

**Response:** `200 OK`
```json
[
  {"date": "2026-01-01", "requests": 150, "avg_latency_ms": 230.5},
  {"date": "2026-01-02", "requests": 175, "avg_latency_ms": 215.3},
  {"date": "2026-01-03", "requests": 200, "avg_latency_ms": 245.8}
]
```

---

### Get Dashboard

Get complete analytics dashboard data.

```
GET /api/v1/analytics/dashboard
```

**Response:** `200 OK`
```json
{
  "summary": { ... },
  "top_endpoints": [ ... ],
  "daily_usage": [ ... ],
  "period_start": "2025-12-07T00:00:00Z",
  "period_end": "2026-01-06T00:00:00Z"
}
```

---

### Get Recent Logs

Get recent API request logs.

```
GET /api/v1/analytics/recent
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | UUID | - | Filter by user |
| `limit` | integer | 50 | Number of logs |
| `status_code` | integer | - | Filter by status |

**Response:** `200 OK`
```json
[
  {
    "id": "...",
    "endpoint": "/api/v1/domains",
    "method": "GET",
    "status_code": 200,
    "latency_ms": 45,
    "ip_address": "192.168.1.100",
    "created_at": "2026-01-06T10:30:00Z",
    "error_message": null
  }
]
```

---

## API Keys API

Manage API keys for authentication.

### Create API Key

Create a new API key.

```
POST /api/v1/api-keys
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | UUID | Yes | User to create key for |

**Request Body:**
```json
{
  "name": "Production Key",
  "rate_limit": 200,
  "expires_at": "2027-01-06T00:00:00Z"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Key name |
| `rate_limit` | integer | No | 100 | Requests per minute |
| `expires_at` | datetime | No | null | Expiration date |

**Response:** `200 OK`
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "name": "Production Key",
  "key": "sk_a1b2c3d4e5f6g7h8i9j0...",
  "key_prefix": "sk_a1b2c",
  "status": "active",
  "rate_limit": 200,
  "created_at": "2026-01-06T10:30:00Z",
  "expires_at": "2027-01-06T00:00:00Z",
  "warning": "Store this key securely. It will not be shown again."
}
```

**Important:** The full key is only returned once at creation. Store it securely.

---

### List API Keys

Get all API keys for a user.

```
GET /api/v1/api-keys
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | UUID | Required | User ID |
| `include_revoked` | boolean | false | Include revoked keys |

**Response:** `200 OK`
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "name": "Production Key",
    "key_prefix": "sk_a1b2c",
    "status": "active",
    "rate_limit": 200,
    "created_at": "2026-01-06T10:30:00Z",
    "last_used_at": "2026-01-06T12:45:00Z",
    "expires_at": "2027-01-06T00:00:00Z"
  }
]
```

Note: The full key is never returned after creation.

---

### Get API Key

Get details of a specific API key.

```
GET /api/v1/api-keys/{key_id}
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | UUID | Yes | User ID for authorization |

---

### Update API Key

Update an API key's settings.

```
PATCH /api/v1/api-keys/{key_id}
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "rate_limit": 500,
  "status": "active"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New name |
| `rate_limit` | integer | New rate limit |
| `status` | string | "active" or "revoked" |

---

### Revoke API Key

Revoke (soft delete) an API key.

```
DELETE /api/v1/api-keys/{key_id}
```

**Response:** `200 OK`
```json
{
  "message": "API key revoked successfully",
  "key_id": "880e8400-e29b-41d4-a716-446655440003"
}
```

---

### Rotate API Key

Create a new key with the same settings and revoke the old one.

```
POST /api/v1/api-keys/{key_id}/rotate
```

**Response:** `200 OK`
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "name": "Production Key (rotated)",
  "key": "sk_x1y2z3...",
  "key_prefix": "sk_x1y2z",
  "status": "active",
  "rate_limit": 200,
  "created_at": "2026-01-06T14:00:00Z"
}
```

---

## WebSocket Endpoints

Real-time communication via WebSocket.

### Planning WebSocket

Connect to receive real-time planning updates.

```
WebSocket: ws://localhost:8000/ws/plan/{session_id}
```

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/plan/session-id');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Message Types Received:**

**Planning Started:**
```json
{
  "type": "planning_started",
  "session_id": "...",
  "timestamp": "2026-01-06T10:30:00Z"
}
```

**Iteration Progress:**
```json
{
  "type": "iteration_progress",
  "iteration": 1,
  "phase": "critiquing",
  "critic": "completeness",
  "timestamp": "2026-01-06T10:30:05Z"
}
```

**Critique Result:**
```json
{
  "type": "critique_result",
  "iteration": 1,
  "critic": "completeness",
  "feedback": "All goals can be achieved",
  "vote": "approve",
  "timestamp": "2026-01-06T10:30:10Z"
}
```

**Plan Updated:**
```json
{
  "type": "plan_updated",
  "iteration": 2,
  "plan": {
    "steps": [...]
  },
  "timestamp": "2026-01-06T10:30:15Z"
}
```

**Planning Completed:**
```json
{
  "type": "planning_completed",
  "session_id": "...",
  "final_plan": { ... },
  "iterations_used": 3,
  "timestamp": "2026-01-06T10:31:00Z"
}
```

---

### Chat WebSocket

Connect for real-time chat updates.

```
WebSocket: ws://localhost:8000/ws/chat/{session_id}
```

**Send Message:**
```json
{
  "type": "message",
  "content": "I want to plan a software release"
}
```

**Receive Message:**
```json
{
  "type": "message",
  "role": "assistant",
  "content": "I can help with that...",
  "timestamp": "2026-01-06T10:30:00Z"
}
```

**State Update:**
```json
{
  "type": "state_update",
  "phase": "gathering_actions",
  "completeness": 0.45,
  "missing_elements": ["preconditions", "effects"]
}
```

---

## Code Examples

### Python

```python
import requests

API_BASE = "http://localhost:8000"
API_KEY = "sk_your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Create domain
response = requests.post(
    f"{API_BASE}/api/v1/domains",
    headers=headers,
    json={
        "name": "My Domain",
        "description": "A test domain"
    }
)
domain = response.json()
print(f"Created domain: {domain['id']}")

# Start planning
response = requests.post(
    f"{API_BASE}/api/v1/planning/sessions",
    headers=headers,
    json={
        "domain_id": domain["id"],
        "problem": "Goal: task_completed"
    }
)
session = response.json()
print(f"Started session: {session['session_id']}")
```

### JavaScript

```javascript
const API_BASE = 'http://localhost:8000';
const API_KEY = 'sk_your-api-key';

async function createDomain(name, description) {
  const response = await fetch(`${API_BASE}/api/v1/domains`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, description }),
  });
  return response.json();
}

async function main() {
  const domain = await createDomain('My Domain', 'A test domain');
  console.log('Created domain:', domain.id);
}

main();
```

### cURL

```bash
# Create domain
curl -X POST "http://localhost:8000/api/v1/domains" \
  -H "X-API-Key: sk_your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Domain", "description": "Test"}'

# Get domain
curl -X GET "http://localhost:8000/api/v1/domains/{domain_id}" \
  -H "X-API-Key: sk_your-api-key"

# Start planning session
curl -X POST "http://localhost:8000/api/v1/planning/sessions" \
  -H "X-API-Key: sk_your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"domain_id": "uuid-here", "problem": "Goal: done"}'
```

---

*Last updated: January 2026*
