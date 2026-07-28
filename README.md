# Auditly – AI Business Health Checker

Auditly is a comprehensive AI-powered system designed to analyze business profiles, audit health, and generate actionable 90-day strategic roadmaps. It leverages multiple intelligent agents (CrewAI) to synthesize business data into a beautifully formatted, pixel-perfect PDF report.

## Project Structure

The project is organized into a full-stack monorepo:

- **`backend/`**: A FastAPI-based Python backend. It handles the core AI logic using CrewAI and LangChain, generates PDF reports using ReportLab, and manages the API endpoints.
- **`frontend/`**: A React application built with Vite. It provides a clean, modern user interface for submitting business profiles, requesting audits, and downloading reports.

## Features

- **Multi-Agent AI Analysis**: Employs an ecosystem of 5 specialized agents to analyze business position, strengths, weaknesses, and growth vectors.
- **Automated SWOT Analysis**: Generates deep SWOT insights and visualizes them on a radar chart.
- **90-Day Roadmap**: Automatically constructs a 3-phase strategic growth plan, including a 90-day growth timeline chart.
- **PDF Report Generation**: Compiles the AI-generated markdown into a professional, Slate & Emerald-themed PDF using a custom modular ReportLab engine.
- **Responsive UI**: Easy-to-use web frontend to input business data and view generated audit reports.

## Getting Started

### Prerequisites

- Node.js (v18+ recommended)
- Python (3.10+ recommended)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables (e.g., API keys for OpenAI/LangChain in a `.env` file).
5. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open the application in your browser at `http://localhost:5173`.
