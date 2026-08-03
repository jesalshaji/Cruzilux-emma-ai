# Emma AI - API Documentation

This document describes the API endpoints provided by the Emma AI Backend.

## Endpoints

### Health Check
- **GET** `/health`
  - Response: `{"status": "ok"}`

### Chat / Conversation
- **POST** `/api/v1/chat`
  - Request Body:
    ```json
    {
      "profile_id": "clinic_demo",
      "message": "Hello, I'd like to book an appointment."
    }
    ```
