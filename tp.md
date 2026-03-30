# Test Procedures (Discovery Engine)

This file contains sample data for testing the **Unified Shopify Recommendation Engine**.

---

## 1. Step 1: Ingest Sample Products
**Endpoint:** `POST /sync/store_test_001/products`

**Payload:**
```json
[
  {
    "product_id": "prod_jacket_001",
    "embedding_source": {
      "title": "Classic Denim Trucker Jacket",
      "brand": "Levi's",
      "category": "Outerwear",
      "description": "The original jean jacket since 1967. A symbol of self-expression for decades, and a great starting point for customization.",
      "tags": ["denim", "blue", "vintage", "jacket"]
    },
    "metadata": {
      "price": 89.50,
      "on_sale": true,
      "color": "Indigo",
      "stock": 45
    }
  },
  {
    "product_id": "prod_shirt_002",
    "embedding_source": {
      "title": "Organic Cotton White T-Shirt",
      "brand": "Everlane",
      "category": "Apparel",
      "description": "A high-quality, sustainable staple for your wardrobe. Made from 100% organic cotton.",
      "tags": ["cotton", "white", "essential", "eco"]
    },
    "metadata": {
      "price": 30.00,
      "on_sale": false,
      "color": "White",
      "stock": 120
    }
  },
  {
    "product_id": "prod_shoes_003",
    "embedding_source": {
      "title": "Air Max Infinity Running Shoes",
      "brand": "Nike",
      "category": "Footwear",
      "description": "High-performance running shoes with responsive cushioning and a breathable mesh upper.",
      "tags": ["sports", "running", "black", "comfortable"]
    },
    "metadata": {
      "price": 120.00,
      "on_sale": true,
      "color": "Black",
      "stock": 15
    }
  }
]
```

---

## 2. Step 2: Test Semantic Search with Filters
**Endpoint:** `POST /search/store_test_001`

**Goal:** Find "affordable blue outerwear" specifically from the brand "Levi's".

**Payload:**
```json
{
  "query_text": "affordable blue outerwear",
  "filters": {
    "brand": ["Levi's"],
    "price": {
      "max": 100
    }
  },
  "limit": 5
}
```

---

## 3. Step 3: Test Similarity Search
**Endpoint:** `POST /search/store_test_001/similar/prod_jacket_001`

**Goal:** Find products similar to the denim jacket that are currently on sale.

**Payload:**
```json
{
  "filters": {
    "on_sale": true
  },
  "limit": 3
}
```
