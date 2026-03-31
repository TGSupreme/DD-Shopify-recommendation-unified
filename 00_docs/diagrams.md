# Project Architecture & UML Diagrams

This document contains the visual representations of the **Unified Shopify Recommendation Engine** using [Mermaid.js](https://mermaid.js.org/).

---

### 1. Component Architecture
Shows the high-level interaction between the core system components and external AI services.

```mermaid
graph TD
    subgraph Shopify_Store [Shopify Storefront/Admin]
        Store[Merchant/Shopper]
    end

    subgraph FastAPI_Application [FastAPI Application]
        Sync[Sync API]
        Search[Search API]
        Recommend[Recommend API]
        QService[Qdrant Service]
        EService[Embedding Service]
    end

    subgraph Qdrant_VDB [Qdrant Vector Database]
        Collection[(Shared Collection)]
        MetaIndex[[Nested Metadata Index]]
        TenantIndex[[Tenant Index: store_id]]
    end

    subgraph External_Services [AI Services]
        Jina((Jina AI API))
    end

    Store -->|Ingest| Sync
    Store -->|Query| Search
    Store -->|History| Recommend

    Sync -->|Vectorize| EService
    Sync -->|Upsert| QService
    
    Search -->|Vectorize| EService
    Search -->|Filter| QService
    
    Recommend -->|Weighted| QService
    
    EService -->|REST| Jina
    QService -->|gRPC/REST| Collection
    Collection --- MetaIndex
    Collection --- TenantIndex
```

---

### 2. Data Model (Class Diagram)
Represents the **Tri-tier Structured Design** and the relationships between identity, search core, and metadata.

```mermaid
classDiagram
    class ProductUpsert {
        +String product_id
        +String title
        +String description
        +String brand
        +String category
        +List~String~ tags
        +ProductMetadata metadata
    }
    
    class ProductMetadata {
        +Float price
        +Float discount
        +Float rating
        +Float weight
        +String color
        +String size
        +String material
        +String gender
        +String season
        +String collection
        +Boolean is_available
    }
    
    class RecommendRequest {
        +List~String~ viewed_ids
        +List~String~ added_to_cart_ids
        +List~String~ purchased_ids
        +Dict filters
        +Int limit
    }
    
    ProductUpsert *-- ProductMetadata : contains
```

---

### 3. Standardized Ingestion Flow (Sequence Diagram)
Illustrates the process of syncing products with the specialized Search Core vs. Metadata split.

```mermaid
sequenceDiagram
    autonumber
    participant Merchant
    participant API as FastAPI (Sync)
    participant Jina as Jina AI (Embeddings)
    participant Qdrant as Qdrant VDB

    Merchant->>API: POST /sync (Tri-tier JSON)
    Note over API: Extract Search Core (Title, Brand, Cat, Tags)
    API->>Jina: Request 768-dim Vectors
    Jina-->>API: Returning Embeddings
    Note over API: Map Commerce Metadata to nested object
    API->>Qdrant: Upsert Points (Vector + Nested Payload)
    Qdrant-->>API: Success
    API-->>Merchant: SyncResponse (Count)
```

---

### 4. Personalized Recommendation Logic (Sequence Diagram)
Shows the weighted interaction logic and the validation against the index.

```mermaid
sequenceDiagram
    autonumber
    participant Shopper
    participant API as FastAPI (Recommend)
    participant QService as Qdrant Service
    participant Qdrant as Qdrant VDB

    Shopper->>API: POST /recommend (User History)
    API->>QService: get_personalized_recommendations()
    
    rect rgb(240, 240, 240)
        Note over QService: Step 1: ID Validation
        QService->>Qdrant: retrieve(IDs)
        Qdrant-->>QService: Existing Points
    end

    rect rgb(240, 240, 240)
        Note over QService: Step 2: Apply Weights
        Note over QService: Viewed(1x), Cart(3x), Purchased(5x)
    end
    
    QService->>Qdrant: recommend(Weighted Positive IDs + Filters)
    Qdrant-->>QService: Scored Matches
    QService-->>API: Results
    API-->>Shopper: JSON Suggestions
```

---

### 5. Multi-tenant Filtering Logic
Shows how the system automatically maps merchant filters to the nested metadata.

```mermaid
graph LR
    A[Merchant Filter: 'price' < 100] --> B{translate_filters}
    C[Merchant Filter: 'brand' = 'Nike'] --> B
    
    B --> D[Qdrant Filter: 'metadata.price' < 100]
    B --> E[Qdrant Filter: 'brand' = 'Nike']
```
