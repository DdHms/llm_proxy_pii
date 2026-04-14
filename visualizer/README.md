# Agent Orchestration Monitor

This is a real-time visualization tool for monitoring agent delegation and tool execution within the LLM Shield proxy.

## Features
- **Real-time Hierarchy**: Visualizes the relationship between the Main Agent and sub-agents.
- **Activity Feed**: Live log of events, tool calls, and strategic decisions.
- **WebSocket Driven**: Uses WebSockets for low-latency updates.

## Accessing the Monitor
The monitor is served by the LLM Shield proxy at `/monitor`.

1. Start the proxy: `python proxy.py`
2. Open `http://localhost:8080/monitor`

## Running the Demo
To see a simulated orchestration process:
1. Open the monitor page.
2. Visit `http://localhost:8080/demo/agent-call` in another tab.
