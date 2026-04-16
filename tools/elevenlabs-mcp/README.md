# ElevenLabs MCP Helper

This is a small local MCP server for voice generation workflows tied to Legendary Leaders AI.

## What it exposes

- `list_voices`: inspect your ElevenLabs account voices.
- `get_models`: inspect available speech models.
- `text_to_speech`: generate speech and return base64 audio that can be written into your asset pipeline.

## Setup

1. Rotate any key that was ever pasted into chat.
2. Copy `.env.example` to `.env`.
3. Put the fresh key into `ELEVENLABS_API_KEY`.
4. Install dependencies with `npm install` in this folder.
5. Run `npm run check`.
6. Run `npm start`.

## Notes

- The server uses stdio transport, which is the normal MCP shape for local tool integration.
- Audio output is returned as base64 so your downstream script or client can decide where to write files.
- This project is intentionally separate from the AoE3 mod files.