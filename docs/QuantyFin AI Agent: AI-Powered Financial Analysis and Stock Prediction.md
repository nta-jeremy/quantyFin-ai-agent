# QuantyFinAI Agent: AI-Powered Financial Analysis (MVP)

## Overview

The QuantyFinAI Agent application is designed as a multi-agent RAG system focused on comprehensive financial analysis with cited answers. The MVP prioritizes retrieval, analysis, and aggregation with citations; advanced prediction can be added in later sprints.

## Core Functionality

The system will analyze a diverse range of data sources to provide insightful predictions:

1.  **Corporate Financial Reports:** In-depth analysis of enterprise financial statements.
2.  **Media and News:** Integration of news articles and media coverage related to finance and economics.
3.  **Regulatory and Legal Frameworks:** Consideration of national and international regulations, legal policies, and economic decrees.
4.  **Economic Indicators:** Analysis of domestic and global economic trends.

By synthesizing information from these sources, the QuantyFinAI Agent provides grounded answers with citations. Prediction features can be introduced incrementally after the MVP.

## Architecture Notes (MVP)

- Dual-engine orchestration: Google ADK and LangGraph; engine is selected at runtime.
- Storage: PostgreSQL (structured) and `pgvector` (embeddings); Redis for short-term session/cache.
- Security: OAuth2/OIDC with JWT; RBAC roles `Admin` and `User`.
