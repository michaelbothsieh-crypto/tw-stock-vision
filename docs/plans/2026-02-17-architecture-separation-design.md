# Design Document: Asynchronous Architecture Separation for Speed & Stability

**Date**: 2026-02-17
**Status**: DRAFT
**Topic**: Decoupling API Read/Write Operations (Option A)

## 1. Problem Statement
The current architecture allows the API to perform blocking I/O operations (fetching data from TWSE/Yahoo/TVScreener) during request handling and server startup.
*   **Cold Start**: `stock_names` fetching blocks server boot (10s+ or timeout).
*   **Request Latency**: Cache misses trigger synchronous external API calls, causing slow responses and potential timeouts on Vercel.
*   **Stability**: External API failures directly impact end-user experience.

## 2. Proposed Solution: Architecture Separation (CQRS-lite)
We will separate the **Read Path** (Client -> API) from the **Write/Update Path** (Worker -> DB).

### 2.1 Architecture Overview

```mermaid
graph TD
    User[Client / Frontend] -->|GET /api/stock| API[Reader API (Serverless)]
    API -->|Read Only| DB[(PostgreSQL)]
    
    Cron[Cron Job / Worker] -->|Scheduled Update| Updater[Updater Service]
    Updater -->|Fetch| External[TWSE / Yahoo / TVS]
    Updater -->|Upsert| DB
```

### 2.2 Key Components

#### A. The Reader API (Fast & Stable)
*   **Responsibility**: Serve data to the frontend.
*   **Behavior**:
    *   **Zero External Requests**: NEVER calls Yahoo/TWSE directly.
    *   **Strictly Database Read**: Selects from `stock_names` and `stock_cache` tables.
    *   **Fast Startup**: Loads `stock_names` from DB (or a static JSON fallback), effectively instant.
    *   **Miss Handling**: If data is missing in DB, return 404 or a "Data Pending" status (future: trigger async update).

#### B. The Updater Service (Reliable Data Ingestion)
*   **Responsibility**: Keep the Database fresh.
*   **Components**:
    1.  **Name Syncer**: Runs daily (e.g., 8:00 AM). Fetches TWSE stock lists and updates `stock_names` table.
    2.  **Market Data Syncer**: Runs frequently (e.g., every 5-10 mins during market hours). Updates data for "Hot/Tracked" stocks.
*   **Execution**:
    *   Can run as a GitHub Action (scheduled).
    *   Can run as a Vercel Cron function (if within timeout limits).
    *   Can be a local script for development.

#### C. Database Schema Changes
*   **`stock_names` Table**: New table to store the master list of stock codes and names (replacing the in-memory dict).
*   **`stock_cache` Table**: Existing table, but receiving updates *only* from the Updater.

## 3. Implementation Steps

### Phase 1: Database Foundation
1.  Create `stock_names` table.
2.  Seed `stock_names` using a one-off script (migrating current logic).

### Phase 2: Updater Service
1.  Refactor `scrapers.py` into standalone scripts/functions that write to DB.
    *   `scripts/sync_names.py`: TWSE -> DB
    *   `scripts/update_market_data.py`: Yahoo/TVS -> DB
2.  Define the "working set" of stocks to update (e.g., Portfolio items + Top 50 volume + User queried recently).

### Phase 3: API Refactoring (The Separation)
1.  Remove `api/services/stock_names.py` startup logic. Refactor to read from `stock_names` table.
2.  Modify `StockService.get_stock_details`:
    *   **Remove** the `fetch_from_yfinance` fallback in the request path.
    *   If cache miss: Return partial data or error (Future: Trigger update queue).

### Phase 4: Frontend adaptation
1.  Implement `SWR` or `React Query` for polling (since data updates in background).
2.  Handle "Data Not Ready" states gracefully.

## 4. Verification Plan
*   **Performance**: API response time should be < 200ms (DB read only).
*   **Stability**: Server startup should be instant (no external HTTP calls).
*   **Data Freshness**: Verify Cron jobs successfully update DB.
