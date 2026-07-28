# homeassistant-customzones

> Generated from repository-local OKF records. The Markdown/YAML bundle remains canonical.

Source: `homeassistant-customzones`

The report separates the connected repository map from detailed component and key-concept views so large bundles remain reviewable.

## Connected-area overview

```mermaid
flowchart LR
    a0["docs · 13 concepts"]
    a1["repository root · 6 concepts"]
    a2["tasks · 1 concepts"]
    a0 -->|links| a1
    a0 -->|links| a2
    a1 -->|links| a0
    a2 -->|links| a0
    classDef default fill:#eef2ff,stroke:#4f46e5,color:#1e1b4b
```

## Connected component 1

### docs

```mermaid
flowchart LR
    n0["Architecture"]:::boundary
    n1["Audit Checklist"]:::boundary
    n2["Codebase Map"]:::boundary
    n3["Contract Delta"]:::boundary
    n4["Core Beliefs"]:::knowledge
    n5["Design"]:::knowledge
    n6["Tech Debt Tracker"]:::knowledge
    n7["Frontend"]:::knowledge
    n8["homeassistant-customzones complete Markdown inventory"]:::knowledge
    n9["homeassistant-customzones documentation map"]:::knowledge
    n10["homeassistant-customzones repository OKF visualization"]:::knowledge
    n11["Plans"]:::knowledge
    n12["Custom Zone Contract"]:::knowledge
    n13["Product Sense"]:::knowledge
    n14["Quality Score"]:::knowledge
    n15["Reliability"]:::knowledge
    n16["Security"]:::knowledge
    n17["Glossary"]:::boundary
    n18["Custom Zone"]:::boundary
    n19["Adopt RKE OKF knowledge format · done"]:::boundary
    n0 -->|links| n9
    n1 -->|links| n9
    n2 -->|links| n9
    n3 -->|links| n9
    n4 -->|links| n9
    n5 -->|links| n9
    n6 -->|links| n18
    n6 -->|links| n0
    n6 -->|links| n7
    n6 -->|links| n12
    n6 -->|links| n9
    n7 -->|links| n9
    n8 -->|links| n0
    n8 -->|links| n1
    n8 -->|links| n2
    n8 -->|links| n3
    n8 -->|links| n4
    n8 -->|links| n5
    n8 -->|links| n6
    n8 -->|links| n7
    n8 -->|links| n9
    n8 -->|links| n10
    n8 -->|links| n11
    n8 -->|links| n12
    n8 -->|links| n13
    n8 -->|links| n14
    n8 -->|links| n15
    n8 -->|links| n16
    n8 -->|links| n17
    n8 -->|links| n18
    n8 -->|links| n19
    n9 -->|links| n18
    n9 -->|links| n8
    n9 -->|links| n0
    n9 -->|links| n2
    n9 -->|links| n6
    n9 -->|links| n11
    n9 -->|links| n4
    n9 -->|links| n5
    n9 -->|links| n7
    n9 -->|links| n17
    n9 -->|links| n3
    n9 -->|links| n12
    n9 -->|links| n14
    n9 -->|links| n15
    n9 -->|links| n13
    n9 -->|links| n16
    n9 -->|links| n1
    n9 -->|links| n19
    n9 -->|links| n10
    n10 -->|links| n9
    n10 -->|links| n8
    n10 -->|links| n19
    n11 -->|links| n9
    n12 -->|links| n9
    n13 -->|links| n9
    n14 -->|links| n9
    n15 -->|links| n9
    n16 -->|links| n9
    n17 -->|links| n9
    n18 -->|links| n12
    n18 -->|links| n0
    n18 -->|links| n15
    n18 -->|links| n9
    n19 -->|links| n9
    n19 -->|links| n10
    classDef task fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef workstream fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef tracker fill:#ffedd5,stroke:#ea580c,color:#431407
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef boundary fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-dasharray:4 3
```

### repository root

```mermaid
flowchart LR
    n0["Architecture"]:::knowledge
    n1["Audit Checklist"]:::knowledge
    n2["Codebase Map"]:::knowledge
    n3["Contract Delta"]:::knowledge
    n4["Tech Debt Tracker"]:::boundary
    n5["homeassistant-customzones complete Markdown inventory"]:::boundary
    n6["homeassistant-customzones documentation map"]:::boundary
    n7["Custom Zone Contract"]:::boundary
    n8["Reliability"]:::boundary
    n9["Glossary"]:::knowledge
    n10["Custom Zone"]:::knowledge
    n0 -->|links| n6
    n1 -->|links| n6
    n2 -->|links| n6
    n3 -->|links| n6
    n4 -->|links| n10
    n4 -->|links| n0
    n4 -->|links| n7
    n4 -->|links| n6
    n5 -->|links| n0
    n5 -->|links| n1
    n5 -->|links| n2
    n5 -->|links| n3
    n5 -->|links| n4
    n5 -->|links| n6
    n5 -->|links| n7
    n5 -->|links| n8
    n5 -->|links| n9
    n5 -->|links| n10
    n6 -->|links| n10
    n6 -->|links| n5
    n6 -->|links| n0
    n6 -->|links| n2
    n6 -->|links| n4
    n6 -->|links| n9
    n6 -->|links| n3
    n6 -->|links| n7
    n6 -->|links| n8
    n6 -->|links| n1
    n7 -->|links| n6
    n8 -->|links| n6
    n9 -->|links| n6
    n10 -->|links| n7
    n10 -->|links| n0
    n10 -->|links| n8
    n10 -->|links| n6
    classDef task fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef workstream fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef tracker fill:#ffedd5,stroke:#ea580c,color:#431407
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef boundary fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-dasharray:4 3
```

### tasks

```mermaid
flowchart LR
    n0["homeassistant-customzones complete Markdown inventory"]:::boundary
    n1["homeassistant-customzones documentation map"]:::boundary
    n2["homeassistant-customzones repository OKF visualization"]:::boundary
    n3["Adopt RKE OKF knowledge format · done"]:::task
    n0 -->|links| n1
    n0 -->|links| n2
    n0 -->|links| n3
    n1 -->|links| n0
    n1 -->|links| n3
    n1 -->|links| n2
    n2 -->|links| n1
    n2 -->|links| n0
    n2 -->|links| n3
    n3 -->|links| n1
    n3 -->|links| n2
    classDef task fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef workstream fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef tracker fill:#ffedd5,stroke:#ea580c,color:#431407
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef boundary fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-dasharray:4 3
```

## Key concept neighbourhoods

### homeassistant-customzones documentation map

```mermaid
flowchart LR
    n0["Architecture"]:::boundary
    n1["Audit Checklist"]:::boundary
    n2["Codebase Map"]:::boundary
    n3["Contract Delta"]:::boundary
    n4["Core Beliefs"]:::boundary
    n5["Design"]:::boundary
    n6["Tech Debt Tracker"]:::boundary
    n7["Frontend"]:::boundary
    n8["homeassistant-customzones complete Markdown inventory"]:::boundary
    n9["homeassistant-customzones documentation map"]:::knowledge
    n10["homeassistant-customzones repository OKF visualization"]:::boundary
    n11["Plans"]:::boundary
    n12["Custom Zone Contract"]:::boundary
    n13["Product Sense"]:::boundary
    n14["Quality Score"]:::boundary
    n15["Reliability"]:::boundary
    n16["Security"]:::boundary
    n17["Glossary"]:::boundary
    n18["Custom Zone"]:::boundary
    n19["Adopt RKE OKF knowledge format · done"]:::boundary
    n0 -->|links| n9
    n1 -->|links| n9
    n2 -->|links| n9
    n3 -->|links| n9
    n4 -->|links| n9
    n5 -->|links| n9
    n6 -->|links| n18
    n6 -->|links| n0
    n6 -->|links| n7
    n6 -->|links| n12
    n6 -->|links| n9
    n7 -->|links| n9
    n8 -->|links| n0
    n8 -->|links| n1
    n8 -->|links| n2
    n8 -->|links| n3
    n8 -->|links| n4
    n8 -->|links| n5
    n8 -->|links| n6
    n8 -->|links| n7
    n8 -->|links| n9
    n8 -->|links| n10
    n8 -->|links| n11
    n8 -->|links| n12
    n8 -->|links| n13
    n8 -->|links| n14
    n8 -->|links| n15
    n8 -->|links| n16
    n8 -->|links| n17
    n8 -->|links| n18
    n8 -->|links| n19
    n9 -->|links| n18
    n9 -->|links| n8
    n9 -->|links| n0
    n9 -->|links| n2
    n9 -->|links| n6
    n9 -->|links| n11
    n9 -->|links| n4
    n9 -->|links| n5
    n9 -->|links| n7
    n9 -->|links| n17
    n9 -->|links| n3
    n9 -->|links| n12
    n9 -->|links| n14
    n9 -->|links| n15
    n9 -->|links| n13
    n9 -->|links| n16
    n9 -->|links| n1
    n9 -->|links| n19
    n9 -->|links| n10
    n10 -->|links| n9
    n10 -->|links| n8
    n10 -->|links| n19
    n11 -->|links| n9
    n12 -->|links| n9
    n13 -->|links| n9
    n14 -->|links| n9
    n15 -->|links| n9
    n16 -->|links| n9
    n17 -->|links| n9
    n18 -->|links| n12
    n18 -->|links| n0
    n18 -->|links| n15
    n18 -->|links| n9
    n19 -->|links| n9
    n19 -->|links| n10
    classDef task fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef workstream fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef tracker fill:#ffedd5,stroke:#ea580c,color:#431407
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef boundary fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-dasharray:4 3
```

### homeassistant-customzones complete Markdown inventory

```mermaid
flowchart LR
    n0["Architecture"]:::boundary
    n1["Audit Checklist"]:::boundary
    n2["Codebase Map"]:::boundary
    n3["Contract Delta"]:::boundary
    n4["Core Beliefs"]:::boundary
    n5["Design"]:::boundary
    n6["Tech Debt Tracker"]:::boundary
    n7["Frontend"]:::boundary
    n8["homeassistant-customzones complete Markdown inventory"]:::knowledge
    n9["homeassistant-customzones documentation map"]:::boundary
    n10["homeassistant-customzones repository OKF visualization"]:::boundary
    n11["Plans"]:::boundary
    n12["Custom Zone Contract"]:::boundary
    n13["Product Sense"]:::boundary
    n14["Quality Score"]:::boundary
    n15["Reliability"]:::boundary
    n16["Security"]:::boundary
    n17["Glossary"]:::boundary
    n18["Custom Zone"]:::boundary
    n19["Adopt RKE OKF knowledge format · done"]:::boundary
    n0 -->|links| n9
    n1 -->|links| n9
    n2 -->|links| n9
    n3 -->|links| n9
    n4 -->|links| n9
    n5 -->|links| n9
    n6 -->|links| n18
    n6 -->|links| n0
    n6 -->|links| n7
    n6 -->|links| n12
    n6 -->|links| n9
    n7 -->|links| n9
    n8 -->|links| n0
    n8 -->|links| n1
    n8 -->|links| n2
    n8 -->|links| n3
    n8 -->|links| n4
    n8 -->|links| n5
    n8 -->|links| n6
    n8 -->|links| n7
    n8 -->|links| n9
    n8 -->|links| n10
    n8 -->|links| n11
    n8 -->|links| n12
    n8 -->|links| n13
    n8 -->|links| n14
    n8 -->|links| n15
    n8 -->|links| n16
    n8 -->|links| n17
    n8 -->|links| n18
    n8 -->|links| n19
    n9 -->|links| n18
    n9 -->|links| n8
    n9 -->|links| n0
    n9 -->|links| n2
    n9 -->|links| n6
    n9 -->|links| n11
    n9 -->|links| n4
    n9 -->|links| n5
    n9 -->|links| n7
    n9 -->|links| n17
    n9 -->|links| n3
    n9 -->|links| n12
    n9 -->|links| n14
    n9 -->|links| n15
    n9 -->|links| n13
    n9 -->|links| n16
    n9 -->|links| n1
    n9 -->|links| n19
    n9 -->|links| n10
    n10 -->|links| n9
    n10 -->|links| n8
    n10 -->|links| n19
    n11 -->|links| n9
    n12 -->|links| n9
    n13 -->|links| n9
    n14 -->|links| n9
    n15 -->|links| n9
    n16 -->|links| n9
    n17 -->|links| n9
    n18 -->|links| n12
    n18 -->|links| n0
    n18 -->|links| n15
    n18 -->|links| n9
    n19 -->|links| n9
    n19 -->|links| n10
    classDef task fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef workstream fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef tracker fill:#ffedd5,stroke:#ea580c,color:#431407
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef boundary fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-dasharray:4 3
```

### Custom Zone

```mermaid
flowchart LR
    n0["Architecture"]:::boundary
    n1["Tech Debt Tracker"]:::boundary
    n2["homeassistant-customzones complete Markdown inventory"]:::boundary
    n3["homeassistant-customzones documentation map"]:::boundary
    n4["Custom Zone Contract"]:::boundary
    n5["Reliability"]:::boundary
    n6["Custom Zone"]:::knowledge
    n0 -->|links| n3
    n1 -->|links| n6
    n1 -->|links| n0
    n1 -->|links| n4
    n1 -->|links| n3
    n2 -->|links| n0
    n2 -->|links| n1
    n2 -->|links| n3
    n2 -->|links| n4
    n2 -->|links| n5
    n2 -->|links| n6
    n3 -->|links| n6
    n3 -->|links| n2
    n3 -->|links| n0
    n3 -->|links| n1
    n3 -->|links| n4
    n3 -->|links| n5
    n4 -->|links| n3
    n5 -->|links| n3
    n6 -->|links| n4
    n6 -->|links| n0
    n6 -->|links| n5
    n6 -->|links| n3
    classDef task fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef workstream fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef tracker fill:#ffedd5,stroke:#ea580c,color:#431407
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef boundary fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-dasharray:4 3
```

### Tech Debt Tracker

```mermaid
flowchart LR
    n0["Architecture"]:::boundary
    n1["Tech Debt Tracker"]:::knowledge
    n2["Frontend"]:::boundary
    n3["homeassistant-customzones complete Markdown inventory"]:::boundary
    n4["homeassistant-customzones documentation map"]:::boundary
    n5["Custom Zone Contract"]:::boundary
    n6["Custom Zone"]:::boundary
    n0 -->|links| n4
    n1 -->|links| n6
    n1 -->|links| n0
    n1 -->|links| n2
    n1 -->|links| n5
    n1 -->|links| n4
    n2 -->|links| n4
    n3 -->|links| n0
    n3 -->|links| n1
    n3 -->|links| n2
    n3 -->|links| n4
    n3 -->|links| n5
    n3 -->|links| n6
    n4 -->|links| n6
    n4 -->|links| n3
    n4 -->|links| n0
    n4 -->|links| n1
    n4 -->|links| n2
    n4 -->|links| n5
    n5 -->|links| n4
    n6 -->|links| n5
    n6 -->|links| n0
    n6 -->|links| n4
    classDef task fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef workstream fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef tracker fill:#ffedd5,stroke:#ea580c,color:#431407
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef boundary fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-dasharray:4 3
```

### homeassistant-customzones repository OKF visualization

```mermaid
flowchart LR
    n0["homeassistant-customzones complete Markdown inventory"]:::boundary
    n1["homeassistant-customzones documentation map"]:::boundary
    n2["homeassistant-customzones repository OKF visualization"]:::knowledge
    n3["Adopt RKE OKF knowledge format · done"]:::boundary
    n0 -->|links| n1
    n0 -->|links| n2
    n0 -->|links| n3
    n1 -->|links| n0
    n1 -->|links| n3
    n1 -->|links| n2
    n2 -->|links| n1
    n2 -->|links| n0
    n2 -->|links| n3
    n3 -->|links| n1
    n3 -->|links| n2
    classDef task fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef workstream fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef tracker fill:#ffedd5,stroke:#ea580c,color:#431407
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef boundary fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-dasharray:4 3
```

### Architecture

```mermaid
flowchart LR
    n0["Architecture"]:::knowledge
    n1["Tech Debt Tracker"]:::boundary
    n2["homeassistant-customzones complete Markdown inventory"]:::boundary
    n3["homeassistant-customzones documentation map"]:::boundary
    n4["Custom Zone"]:::boundary
    n0 -->|links| n3
    n1 -->|links| n4
    n1 -->|links| n0
    n1 -->|links| n3
    n2 -->|links| n0
    n2 -->|links| n1
    n2 -->|links| n3
    n2 -->|links| n4
    n3 -->|links| n4
    n3 -->|links| n2
    n3 -->|links| n0
    n3 -->|links| n1
    n4 -->|links| n0
    n4 -->|links| n3
    classDef task fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef workstream fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef tracker fill:#ffedd5,stroke:#ea580c,color:#431407
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef boundary fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-dasharray:4 3
```

## Legend

- Blue: task
- Purple: workstream
- Orange: tracker profile
- Green: durable knowledge
- Dashed neutral nodes: neighbouring context repeated from another area or key-concept view
- Time references: edges to addressable `Task.time[]` fragments
- Arrows: structured relationships or repository-local Markdown links
