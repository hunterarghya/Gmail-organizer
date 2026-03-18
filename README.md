# Gmail AI Organizer

An AI-powered Gmail automation system that uses agent-based workflows to intelligently process, classify, and act on emails.

---

## Overview

This project builds an **agent-driven backend system** that connects to a user's Gmail account and performs automated inbox management tasks such as triaging, cleanup, and categorization.

Designed with **modularity, extensibility, and real-world automation** in mind.

---

## Core Capabilities

- Scan and analyze inbox using AI agents
- Classify emails (important, OTPs, spam, etc.)
- Draft replies to urgent mails
- Perform cleanup operations (delete, archive, filter)
- Return structured summaries of inbox state
- Supports upgrade to real-time streaming execution

---

## System Design (Agent Architecture)

### Flow

User Action → API Endpoint → Agent Orchestrator → Task Pipeline → Output

---

### Agents

#### Auditor Agent

- Reads inbox data
- Extracts metadata (sender, subject, patterns)
- Classifies emails into categories
- Produces structured intermediate output

#### Action Agent (Executor)

- Consumes auditor output
- Decides actions:
  - keep
  - delete
  - archive
- Executes Gmail operations via tools

---

### Task Pipeline

1. Fetch emails from Gmail API
2. Pass emails to Auditor Agent
3. Generate structured classification
4. Feed into Action Agent
5. Perform actions (cleanup / tagging)
6. Return final summary

---

### Design Principles

- Separation of concerns (analysis vs execution)
- Composable agents (easy extensibility)
- Tool abstraction for Gmail operations
- Async-friendly architecture
- Stateless API design

---

## Execution Modes

### Standard (stdout capture)

- Runs full pipeline
- Returns output after completion
- Simple and reliable

### Streaming (planned)

- Real-time logs via SSE
- Better observability
- Production-ready UX

---

## Tech Stack

- FastAPI (backend)
- CrewAI (agent orchestration)
- Google OAuth 2.0 (authentication)
- Python

---

## Getting Started

### Install dependencies

    pip install -r requirements.txt

### Configure environment

    GROQ_API_KEY=your_key
    GOOGLE_CLIENT_ID=your_client_id
    GOOGLE_CLIENT_SECRET=your_secret

### Run server

    uvicorn src.main:app --reload

### Access

    http://localhost:8000/static/index.html

---

## UPCOMING FEATURES

### Automation Features

- Auto-label emails (smart tagging)
- Auto-delete low-value emails
- Smart archive system
- Email scheduling (send later / reminders)
- Rule-based filtering (custom pipelines)

---

### Intelligence Upgrades

- Learning from user behavior (adaptive agents)
- Priority scoring system
- Context-aware summarization
- Multi-inbox aggregation

---

### System Enhancements

- SSE streaming for real-time logs
- Queue-based processing (Celery / Redis)
- Retry + failure handling
- Rate-limit aware Gmail operations

---

## Why This Project

Demonstrates:

- Real-world OAuth integration
- Agent-based system design
- Backend API architecture
- Workflow orchestration
- Practical AI automation

---

## Author

Arghya Malakar  
Final Year CSE | Backend + Mobile Dev | Aspiring Startup Engineer
