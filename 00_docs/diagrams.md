# Project Architecture & Logic Diagrams

This document contains the visual representations of the **Unified Shopify Recommendation Engine** using [Mermaid.js](https://mermaid.js.org/).

---

### 1. High-Level System Workflow (Flowchart)
This diagram shows the general flow of data from ingestion to recommendation.

```mermaid
graph TD
    A[Shopify Store] -->|1. Ingest Products| B(FastAPI Service)
    B -->|2. Vectorize| C{Embedding Model}
    C -->|3. Store Vectors + Metadata| D[(Vector Database)]
    
    E[Customer Interaction] -->|4. Request Recommendations| B
    B -->|5. Weighted Calculation| F[User Interest Vector]
    F -->|6. Search| D
    D -->|7. Recommended Products| B
    B -->|8. Return Results| A
```

---

### 2. Recommendation Sequence (Sequence Diagram)
This diagram illustrates the step-by-step logic of a recommendation request.

```mermaid
sequenceDiagram
    autonumber
    participant Store as Shopify Store
    participant API as FastAPI Engine
    participant VDB as Vector Database

    Store->>API: GET /recommend (User History)
    Note over API: Apply Weights (Purchased > Cart > Viewed)
    API->>VDB: Query Nearest Neighbors
    VDB-->>API: Top K Matches
    API-->>Store: JSON Recommendations
```

---

### 3. How to View and Edit These Diagrams
*   **VS Code:** Install the **"Markdown Preview Mermaid Support"** extension to see these diagrams live.
*   **GitHub/GitLab:** These diagrams are rendered automatically in the web interface.
*   **Mermaid Live Editor:** You can copy-paste the code blocks into [Mermaid.live](https://mermaid.live/) to export them as PNG/SVG.
