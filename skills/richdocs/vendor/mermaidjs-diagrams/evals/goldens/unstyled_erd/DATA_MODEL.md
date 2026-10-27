# Order data model

A customer places orders. Each order holds one or more lines, each line names a
catalogue product, and an order is settled by one or more payments.

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_LINE : contains
    PRODUCT ||--o{ ORDER_LINE : "appears on"
    ORDER ||--o{ PAYMENT : "settled by"

    CUSTOMER {
        uuid id PK
        string email
        string display_name
        timestamp created_at
    }
    ORDER {
        uuid id PK
        uuid customer_id FK
        string status
        timestamp placed_at
    }
    ORDER_LINE {
        uuid order_id FK
        uuid product_id FK
        int quantity
        int unit_price_cents
    }
    PRODUCT {
        uuid id PK
        string sku
        string title
    }
    PAYMENT {
        uuid id PK
        uuid order_id FK
        int amount_cents
        string provider
    }

    %% erDiagram paints fill: on even attribute rows only, so no color: here.
    %% Translucent fills tint with the theme; opaque strokes carry the hue.
    classDef party       fill:#1d4ed855,stroke:#3b82f6,stroke-width:2px
    classDef transaction fill:#b4530966,stroke:#d97706,stroke-width:2px
    classDef catalogue   fill:#04785755,stroke:#10b981,stroke-width:2px
    class CUSTOMER party
    class ORDER,ORDER_LINE,PAYMENT transaction
    class PRODUCT catalogue
```
