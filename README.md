# Google Maps Agents with Google ADK

Two conversational Google Maps agents built with the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/):

- **Maps_Agent** calls the Google Places API and Routes API directly through Python tools.
- **MCP_Maps_Agent** connects to Google's hosted Google Maps MCP server through ADK's MCP toolset.

Ask questions in natural language to find places, get route information, and explore businesses near a journey. The agents use Maps tools for location results rather than making up distances, durations, or business details.

## Features

| Agent | How it accesses Maps | Capabilities |
|---|---|---|
| `Maps_Agent` | Direct Places API and Routes API calls | Route distance and duration for driving, walking, bicycling, and transit; search for places near a route's midpoint |
| `MCP_Maps_Agent` | Google's hosted Maps MCP server | Search places and businesses, calculate routes, and resolve location names using the tools exposed by the MCP server |

Both agents are configured to return relevant Maps links when available. API availability, enabled services, and Google Maps Platform billing may affect results. The MCP agent does not provide weather forecasts.

## Project structure

```text
.
├── Maps_Agent/
│   └── agent.py           # Direct Places and Routes API agent
├── MCP_Maps_Agent/
│   └── agent.py           # Google Maps MCP agent
├── output/
│   ├── ADK_with_MCP.png
│   ├── With_MCP_GUI.png
│   └── Without_MCP_GUI.png
├── DOCUMENTATION.pdf
├── GOOGLE_MAPS_API_KEY_SETUP.pdf
└── requirements.txt
```

## Requirements

- Python
- A Google AI API key for the Gemini model used by ADK (or your configured Vertex AI credentials)
- A Google Maps Platform API key with the required Maps services enabled
- Billing enabled for the Google Cloud project, if required by the APIs you use

See [Google Maps API key setup](./GOOGLE_MAPS_API_KEY_SETUP.pdf) for key setup guidance.

## Setup

1. Clone the repository and open a terminal in its root directory.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   On macOS or Linux:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install the project dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Create a `.env` file in the repository root and add your keys:

   ```dotenv
   GOOGLE_API_KEY=your_gemini_api_key
   MAPS_API_KEY=your_google_maps_platform_api_key
   # Optional: overrides the model default configured in the agent
   GEMINI_MODEL=gemini-3.8-flash
   ```

   `GOOGLE_API_KEY` is used by ADK to access Gemini when using the Gemini Developer API. If you use Vertex AI, configure ADK's Vertex AI authentication instead. `MAPS_API_KEY` is used by both agents.

   For `Maps_Agent`, enable the Google Maps Platform **Routes API** and **Places API** for the Cloud project associated with the Maps key. For `MCP_Maps_Agent`, make sure the key/project is authorized to use Google's hosted Maps MCP service. Follow the setup document for details.

   Keep `.env` private. It is ignored by Git; do not commit or share API keys.

## Run an agent

From the repository root, start either agent in the ADK command-line interface:

```bash
adk run Maps_Agent
```

```bash
adk run MCP_Maps_Agent
```

To open ADK's local development UI and select an agent:

```bash
adk web
```

## Example prompts

For `Maps_Agent`:

- "Calculate the driving route from Marina Beach, Chennai to Chennai Central."
- "Find restaurants near the route from Marina Beach to Chennai Central."
- "Give me walking directions from [origin] to [destination]."

For `MCP_Maps_Agent`:

- "Find five restaurants near Marina Beach, Chennai."
- "Find petrol stations near T Nagar, Chennai."
- "How do I get from Marina Beach to Chennai Central?"

## Screenshots

### Direct Maps API agent
<img width="1907" height="592" alt="Without_MCP_GUI" src="https://github.com/user-attachments/assets/c35796e4-334a-4495-930c-b711a3738d9a" />



### Maps MCP agent
<img width="1902" height="947" alt="With_MCP_GUI" src="https://github.com/user-attachments/assets/afe23fbf-b616-4e56-bd3c-d91ef48b30c8" />



### MCP agent run in the terminal

<img width="1450" height="572" alt="ADK_with_MCP" src="https://github.com/user-attachments/assets/161cc1bf-3fed-429e-a9de-4dfb6fca7a14" />


## Documentation

- [Project documentation](./DOCUMENTATION.pdf)
- [Google Maps API key setup](./GOOGLE_MAPS_API_KEY_SETUP.pdf)

## Security

Never commit API keys, `.env` files, or credentials. Restrict your keys using the Google Cloud API and application restrictions appropriate for your setup, and monitor usage in Google Cloud.
