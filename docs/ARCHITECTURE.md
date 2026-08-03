# Emma AI - Architecture Overview

This document details the technical architecture and component relationships of the Emma AI system.

## Overview
Emma AI is an AI automation bot platform designed to support multiple business profiles (clinics, barbers, hotels, etc.) with custom agent workflows.

## High-Level Components
- **Frontend**: Client interface for user interactions.
- **Backend (Python/FastAPI)**:
  - `app/routes`: API endpoints.
  - `app/ai`: AI orchestrator, model clients, and chain execution.
  - `app/services`: Core application logic.
  - `app/models`: Data models and schemas.
  - `app/database`: Database abstraction layer.
  - `app/prompts`: Prompt templates and system instructions.
  - `app/tools`: Custom tools for AI function calling.
  - `app/business`: Logic handling domain-specific business profiles.
  - `app/utils`: Shared helper functions.
- **Business Profiles**: Configurations, prompts, and knowledge bases per business demo.
