# Database Schemas

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
| `metadata`     | `JSONB`            | `NULL`                 | Required keys for MVP: `source`, `source_date`, `doc_type`, `company_name`, `ticker`; optional: `url`, `title` |

**Notes:**

* The `VECTOR(1536)` type is an example (e.g., OpenAI `text-embedding-ada-002`). Dimension depends on the chosen model.
* Ensure metadata is populated to support traceability and cited answers per MVP.
