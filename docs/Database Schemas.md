# Database Schema

The QuantyFinAI Agent system utilizes both a traditional relational database (PostgresDB) for structured data and a vector database (Postgres Vector Database, e.g., `pgvector`) for unstructured data embeddings. This dual-database approach supports efficient storage and retrieval for both conventional and AI-driven data requirements.

## 1. PostgresDB (Structured Data)

This database will store structured information critical for financial analysis, user management, and system operations. Below is a conceptual schema for key tables:

### `users` Table

Stores user authentication and profile information.

| Column Name    | Data Type          | Constraints            | Description                               |
| :------------- | :----------------- | :--------------------- | :---------------------------------------- |
| `id`           | `UUID`             | `PRIMARY KEY`          | Unique identifier for the user            |
| `username`     | `VARCHAR(255)`     | `UNIQUE`, `NOT NULL`   | User's chosen username                    |
| `email`        | `VARCHAR(255)`     | `UNIQUE`, `NOT NULL`   | User's email address                      |
| `password_hash`| `VARCHAR(255)`     | `NOT NULL`             | Hashed password                           |
| `created_at`   | `TIMESTAMP`        | `DEFAULT NOW()`        | Timestamp of user creation                |
| `updated_at`   | `TIMESTAMP`        | `DEFAULT NOW()`        | Last update timestamp                     |
| `role_id`      | `INTEGER`          | `FOREIGN KEY`          | References `roles.id`                     |

### `roles` Table

Defines the roles for Role-Based Access Control (RBAC).

| Column Name | Data Type      | Constraints            | Description                       |
| :---------- | :------------- | :--------------------- | :-------------------------------- |
| `id`        | `SERIAL`       | `PRIMARY KEY`          | Unique identifier for the role    |
| `name`      | `VARCHAR(50)`  | `UNIQUE`, `NOT NULL`   | Name of the role (e.g., 'Admin')  |
| `description`| `TEXT`         | `NULL`                 | Description of the role           |

### `companies` Table

Stores basic information about companies being tracked.

| Column Name    | Data Type          | Constraints            | Description                               |
| :------------- | :----------------- | :--------------------- | :---------------------------------------- |
| `id`           | `UUID`             | `PRIMARY KEY`          | Unique identifier for the company         |
| `name`         | `VARCHAR(255)`     | `UNIQUE`, `NOT NULL`   | Company's official name                   |
| `ticker_symbol`| `VARCHAR(10)`      | `UNIQUE`, `NOT NULL`   | Stock ticker symbol                       |
| `industry`     | `VARCHAR(100)`     | `NULL`                 | Industry sector of the company            |
| `country`      | `VARCHAR(100)`     | `NULL`                 | Country of operation                      |
| `founded_date` | `DATE`             | `NULL`                 | Date the company was founded              |

### `financial_reports` Table

Stores metadata and links to financial reports.

| Column Name    | Data Type          | Constraints            | Description                               |
| :------------- | :----------------- | :--------------------- | :---------------------------------------- |\n| `id`           | `UUID`             | `PRIMARY KEY`          | Unique identifier for the report          |
| `company_id`   | `UUID`             | `FOREIGN KEY`          | References `companies.id`                 |
| `report_type`  | `VARCHAR(50)`      | `NOT NULL`             | Type of report (e.g., 'Annual', 'Quarterly') |
| `period_start` | `DATE`             | `NOT NULL`             | Start date of the reporting period        |
| `period_end`   | `DATE`             | `NOT NULL`             | End date of the reporting period          |
| `filing_date`  | `DATE`             | `NOT NULL`             | Date the report was filed                 |
| `document_url` | `TEXT`             | `NOT NULL`             | URL to the original report document       |
| `summary`      | `TEXT`             | `NULL`                 | AI-generated summary of the report        |

### `stock_data` Table

Stores historical stock price data.

| Column Name    | Data Type          | Constraints            | Description                               |
| :------------- | :----------------- | :--------------------- | :---------------------------------------- |
| `id`           | `UUID`             | `PRIMARY KEY`          | Unique identifier for the stock record    |
| `company_id`   | `UUID`             | `FOREIGN KEY`          | References `companies.id`                 |
| `date`         | `DATE`             | `NOT NULL`             | Date of the stock data                    |
| `open_price`   | `NUMERIC(10, 2)`   | `NOT NULL`             | Opening price of the stock                |
| `close_price`  | `NUMERIC(10, 2)`   | `NOT NULL`             | Closing price of the stock                |
| `high_price`   | `NUMERIC(10, 2)`   | `NOT NULL`             | Highest price of the stock                |
| `low_price`    | `NUMERIC(10, 2)`   | `NOT NULL`             | Lowest price of the stock                 |
| `volume`       | `BIGINT`           | `NOT NULL`             | Trading volume                            |

## 2. Postgres Vector Database (Unstructured Data Embeddings)

This database, likely implemented using the `pgvector` extension for PostgreSQL, will store vector embeddings of various unstructured documents. These embeddings enable semantic search and retrieval for the RAG system.

### `document_embeddings` Table (Conceptual)

Stores vector representations of documents and their metadata.

| Column Name    | Data Type          | Constraints            | Description                               |
| :------------- | :----------------- | :--------------------- | :---------------------------------------- |
| `id`           | `UUID`             | `PRIMARY KEY`          | Unique identifier for the document chunk  |
| `source_type`  | `VARCHAR(50)`      | `NOT NULL`             | Type of source (e.g., 'news', 'report', 'legal') |
| `source_id`    | `UUID`             | `NULL`                 | Optional: ID linking to original source (e.g., `financial_reports.id`) |
| `content_chunk`| `TEXT`             | `NOT NULL`             | The text chunk that was embedded          |
| `embedding`    | `VECTOR(1536)`     | `NOT NULL`             | The vector embedding of the content chunk (dimension depends on embedding model) |
| `created_at`   | `TIMESTAMP`        | `DEFAULT NOW()`        | Timestamp of embedding creation           |
| `metadata`     | `JSONB`            | `NULL`                 | Additional metadata (e.g., URL, title, date) |

**Note:** The `VECTOR(1536)` data type is an example, assuming an embedding model like OpenAI's `text-embedding-ada-002` which produces 1536-dimensional vectors. This dimension will vary based on the chosen embedding model.
