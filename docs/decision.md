# Architecture Decisions

## ADR-001
Date: 2026-08-03

Decision:
Store AI model names in environment variables with sensible defaults.

Reason:
Allows deployment configuration without changing code.

Alternatives:
- Hardcoded model names
- JSON configuration file

Chosen because:
Environment variables are the standard for deployments and cloud platforms
