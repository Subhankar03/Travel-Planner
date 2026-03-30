# ✈️ Multi-Agent Travel Planner

A multi-agent AI travel assistant that plans entire trips — flights, stays, places, and routes — in one conversation.

---

## 📌 Overview

Planning a trip usually involves juggling multiple platforms for flights, hotels, and local research. This project solves that by combining everything into a single AI-driven system.

It is a multi-agent travel planner that enables users to plan trips using natural language. From finding flights and hotels to discovering attractions and generating routes, everything is handled through a single conversational interface, where specialized agents collaborate to produce a unified travel plan.

---

## ✨ Key Features

- **Natural language trip planning**
- **Multi-agent architecture** with task specialization
- **Flight and hotel search** using real-time data
- **Local attractions and restaurant discovery**
- **Route planning** between locations (maps integration)
- **FastAPI Backend** exposing a responsive, asynchronous API
- **Real-time Streaming** via the Vercel AI SDK (`x-vercel-ai-ui-message-stream: v1`) protocol over SSE
- **Observability** with detailed execution logs

---

## 🧠 Architecture

```mermaid
flowchart TD
    User([User]) --> Frontend[React Frontend]
    Frontend -->|SSE Stream| FastAPI[FastAPI Backend]
    FastAPI --> LangGraph[LangGraph State Machine]
    LangGraph --> Supervisor[Supervisor Agent]
  
    Supervisor -->|Booking/Itinerary| Booking[Travel Booking Agent]
    Supervisor -->|Local Info/Research| Research[Local Research Agent]
  
    Booking --> SerpFlights[SerpAPI: Flights]
    Booking --> SerpHotels[SerpAPI: Hotels]
  
    Research --> SerpLocal[SerpAPI: Local]
  
    Booking --> Supervisor
    Research --> Supervisor
    LangGraph --> FastAPI
```

### Agent Workflow

- **Supervisor Agent**: Routes user queries to the appropriate specialized agent.
- **Booking Agent**: Handles flights, hotels, and itinerary planning.
- **Research Agent**: Handles local discovery (restaurants, attractions, routes).
- **Tool Nodes**: Execute remote API calls via SerpAPI.
- **Checkpointer**: Uses `MemorySaver` to persist conversation histories for the lifespan of the server process.

---

## 🛠️ Tech Stack

- **Backend core**: Python, LangGraph, standard `MemorySaver` checkpointer
- **LLM**: Google Gemini
- **Tools**: SerpAPI (Flights, Hotels, Local search), Google Maps
- **API Server**: FastAPI, Uvicorn
- **Streaming**: Vercel AI SDK DataStream Protocol
- **Legacy UI**: Streamlit
- **Upcoming UI**: React, Vite, TailwindCSS

---

## 📂 Project Structure

- **`backend/`** — All server-side logic
  - `server.py` — Main FastAPI application serving `/api/chat` and static frontend files
  - `agent.py` — LangGraph multi-agent workflow definition
  - `state.py` — Graph state and schema definitions
  - `tools.py` — SerpAPI & Google Maps tool integrations
  - `routes/chat.py` — Chat endpoint handling HTTP streaming
  - `core/graph.py` — Compiles the LangGraph state machine with the MemorySaver checkpointer
  - `core/stream_formatter.py` — Translates LangGraph `astream` events into Vercel AI SDK SSE parts
  - `models/schemas.py` — Pydantic request/response models
  - `prompts/` — Markdown-based system prompts for each agent
  - `serpapi_schemas/` — JSON schemas for SerpAPI hotel amenities and property types
  - `utils/` — Shared backend utility functions
- **`app.py`** — Legacy Streamlit frontend UI (V1)
- **`main.py`** — Legacy CLI interface for testing
- **`logger.py`** — Logging and observability system
- **`serpapi_results/`** — Cached SerpAPI response samples for testing
- **`pyproject.toml`** — Dependencies managed by `uv`

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Subhankar03/Travel-Planner.git
cd Travel-Planner
```

### 2. Install dependencies (using uv)

```bash
uv sync
```

> `uv` automatically manages the virtual environment and resolves dependencies seamlessly.

### 3. Setup environment variables

Create a `.env` file in the root directory:

```env
SERPAPI_KEY=your_serpapi_key
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

---

## ▶️ Usage

### Run the FastAPI Backend

Start the heavily optimized asynchronous backend which listens on port 8000:

```bash
uv run uvicorn backend.server:app --host 0.0.0.0 --port 8000
```

### Legacy Streamlit App

If you want to run the original V1 prototype UI:

```bash
uv run streamlit run app.py
```

---

## 💬 Example Prompts

- "Plan a 5-day trip from Kolkata to Goa next month with a total budget under ₹25,000. Find the cheapest flights (layovers are fine) and suggest budget-friendly hotels near popular beaches. Also include a simple day-wise itinerary with must-visit spots."
- "I’m visiting Jaipur for 3 days with my family and want premium accommodation. Find highly rated 5-star hotels and suggest nearby attractions, including forts, cultural spots, and good restaurants for authentic Rajasthani food."
- "I’ll be in Bangalore for a weekend and want to explore the city. Suggest top-rated cafes, coworking-friendly spots, and popular tourist attractions, along with a rough plan to cover them efficiently."

---

## 📊 Output Capabilities

The system generates:

- Flight options with pricing and booking links
- Hotel recommendations with amenities and images
- Local attractions, restaurants, and reviews
- Structured itinerary suggestions
- Route guidance between locations (maps integration)

---

## 🔌 APIs Used

- SerpAPI (Google Flights, Hotels, Local Search)
- Google Maps Platform
- Google Gemini (LLM reasoning and agent coordination)

---

## 📈 Observability

The system includes a logging module that tracks:

- User queries
- Agent decisions
- Tool calls and outputs
- Final AI responses

Logs are stored per day and automatically cleaned up after 7 days.

---

## 🚧 Limitations

- Depends on external APIs (rate limits and latency)
- Pricing data may not always be real-time accurate
- MemorySaver is ephemeral — conversations reset when the FastAPI server restarts

---

## 🔮 Future Improvements

- React + Vite custom interactive frontend
- Persistent memory for long-term personalized recommendations using a database checkpointer
- Advanced itinerary optimization
- Improved route visualization and map interactions

---

## 📜 License

MIT License

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
