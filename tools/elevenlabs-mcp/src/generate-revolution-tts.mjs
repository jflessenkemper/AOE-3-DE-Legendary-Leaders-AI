import "dotenv/config";

import fs from "node:fs";
import path from "node:path";

const root = path.resolve(new URL("../../..", import.meta.url).pathname);
const apiKey = process.env.ELEVENLABS_API_KEY;
const modelId = process.env.ELEVENLABS_MODEL_ID || "eleven_multilingual_v2";
const outputFormat = process.env.ELEVENLABS_OUTPUT_FORMAT || "mp3_44100_128";
const voiceMapPath = path.join(root, "tools", "elevenlabs-mcp", "voice-map.json");
const manifestPaths = [
  path.join(root, "resources", "audio", "standard_leader_manifest.json"),
  path.join(root, "resources", "audio", "revolution_leader_manifest.json")
];

if (!apiKey) {
  console.error("ELEVENLABS_API_KEY is required.");
  process.exit(1);
}

if (!fs.existsSync(voiceMapPath)) {
  console.error("voice-map.json is required. Copy voice-map.example.json and fill in voice IDs.");
  process.exit(1);
}

const voiceMap = JSON.parse(fs.readFileSync(voiceMapPath, "utf8"));
const manifest = {
  leaders: manifestPaths.flatMap((manifestPath) => JSON.parse(fs.readFileSync(manifestPath, "utf8")).leaders)
};

async function speak(voiceId, text, settings) {
  const response = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?output_format=${encodeURIComponent(outputFormat)}`,
    {
      method: "POST",
      headers: {
        "xi-api-key": apiKey,
        "Content-Type": "application/json",
        Accept: "audio/mpeg"
      },
      body: JSON.stringify({
        text,
        model_id: modelId,
        voice_settings: {
          stability: settings.stability,
          similarity_boost: settings.similarityBoost,
          style: settings.style,
          use_speaker_boost: settings.useSpeakerBoost
        }
      })
    }
  );

  if (!response.ok) {
    throw new Error(`${response.status} ${await response.text()}`);
  }

  return Buffer.from(await response.arrayBuffer());
}

for (const leader of manifest.leaders) {
  const voiceId = voiceMap[leader.leaderKey];
  if (!voiceId) {
    console.warn(`Skipping ${leader.leaderKey}: no voice ID in voice-map.json`);
    continue;
  }

  const outDir = path.join(root, "sound", "voices", leader.leaderKey);
  fs.mkdirSync(outDir, { recursive: true });

  const lines = [
    ...leader.insults.map((text, index) => ({ name: `insult_${index + 1}.mp3`, text })),
    ...leader.compliments.map((text, index) => ({ name: `compliment_${index + 1}.mp3`, text }))
  ];

  for (const line of lines) {
    const audio = await speak(voiceId, line.text, leader.voice);
    fs.writeFileSync(path.join(outDir, line.name), audio);
    console.log(`wrote ${leader.leaderKey}/${line.name}`);
  }
}