# Graph Report - aetcg-platform  (2026-10-02)

## Corpus Check
- Corpus is ~2,980 words - fits in a single context window. You may not need a graph.

## Summary
- 86 nodes · 135 edges · 11 communities (4 shown, 7 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Data Validation and Testing
- Orchestration and Agent System
- Web Application and Worker Services
- Middleware and Security Components
- Configuration Validation

## God Nodes (most connected - your core abstractions)
1. `DataSanitizationPipeline` - 11 edges
2. `StateMachineOrchestrator` - 8 edges
3. `TriageAgent` - 8 edges
4. `ComplianceCriticAgent` - 8 edges
5. `TicketIngestionSchema` - 7 edges
6. `rate_limit_middleware()` - 5 edges
7. `ingest_ticket()` - 5 edges
8. `AppSettings` - 4 edges
9. `check_rate_limit()` - 4 edges
10. `add_security_headers()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `ingest_ticket()` --uses--> `TicketIngestionSchema`  [INFERRED]
  main.py → pipeline/validation.py
- `StateMachineOrchestrator` --uses--> `ComplianceCriticAgent`  [INFERRED]
  pipeline/orchestrator.py → services/agents.py
- `StateMachineOrchestrator` --uses--> `TriageAgent`  [INFERRED]
  pipeline/orchestrator.py → services/agents.py
- `process_pipeline_task()` --calls--> `StateMachineOrchestrator`  [EXTRACTED]
  worker.py → pipeline/orchestrator.py
- `test_pydantic_corporate_domain_enforcement()` --calls--> `TicketIngestionSchema`  [EXTRACTED]
  tests/test_pipeline.py → pipeline/validation.py

## Import Cycles
- None detected.

## Communities (11 total, 7 thin omitted)

### Community 0 - "Data Validation and Testing"
Cohesion: 0.13
Nodes (6): DataSanitizationPipeline, replace_func(), TicketIngestionSchema, test_enhanced_pii_scrubbing(), test_pydantic_corporate_domain_enforcement(), test_regex_pii_scrubbing_pipeline()

### Community 1 - "Orchestration and Agent System"
Cohesion: 0.18
Nodes (3): StateMachineOrchestrator, ComplianceCriticAgent, TriageAgent

### Community 2 - "Web Application and Worker Services"
Cohesion: 0.17
Nodes (4): get_state(), ingest_ticket(), process_pipeline_task(), queue_triage_job()

### Community 4 - "Middleware and Security Components"
Cohesion: 0.24
Nodes (4): add_security_headers(), administrative_approval_gate(), check_rate_limit(), rate_limit_middleware()

## Knowledge Gaps
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DataSanitizationPipeline` connect `Data Validation and Testing` to `Orchestration and Agent System`, `Core Configuration and Libraries`?**
  _High betweenness centrality (0.225) - this node is a cross-community bridge._
- **Why does `TriageAgent` connect `Orchestration and Agent System` to `Core Configuration and Libraries`, `OpenAI Integration and Agent Initialization`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Why does `ComplianceCriticAgent` connect `Orchestration and Agent System` to `Core Configuration and Libraries`, `OpenAI Integration and Agent Initialization`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `StateMachineOrchestrator` (e.g. with `DataSanitizationPipeline` and `ComplianceCriticAgent`) actually correct?**
  _`StateMachineOrchestrator` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Data Validation and Testing` be split into smaller, more focused modules?**
  _Cohesion score 0.1286549707602339 - nodes in this community are weakly interconnected._