import fs from "node:fs";
import path from "node:path";

const root = path.resolve(new URL("../../..", import.meta.url).pathname);
const readmePath = path.join(root, "README.md");
const manifestPaths = [
  {
    label: "Standard Leaders",
    filePath: path.join(root, "resources", "audio", "standard_leader_manifest.json")
  },
  {
    label: "Revolution Leaders",
    filePath: path.join(root, "resources", "audio", "revolution_leader_manifest.json")
  }
];

const beginMarker = "<!-- BEGIN GENERATED AUDIO INDEX -->";
const endMarker = "<!-- END GENERATED AUDIO INDEX -->";

function makeClipLinks(leaderKey) {
  const basePath = `sound/voices/${leaderKey}`;
  return [
    `[Insult 1](${basePath}/insult_1.mp3)`,
    `[Insult 2](${basePath}/insult_2.mp3)`,
    `[Compliment 1](${basePath}/compliment_1.mp3)`,
    `[Compliment 2](${basePath}/compliment_2.mp3)`
  ].join("<br>");
}

function makeTable(label, leaders) {
  const rows = leaders.map((leader) => {
    const portrait = `<img src="${leader.smallPortraitFile}" alt="${leader.leaderName} portrait" width="40">`;
    return `| ${portrait} | ${leader.nation} | ${leader.leaderName} | ${makeClipLinks(leader.leaderKey)} |`;
  });

  return [
    `<details>`,
    `<summary>${label} (${leaders.length})</summary>`,
    "",
    "| Portrait | Nation | Leader | Clip Links |",
    "| --- | --- | --- | --- |",
    ...rows,
    "",
    `</details>`
  ].join("\n");
}

function buildSection() {
  const sections = manifestPaths.map(({ label, filePath }) => {
    const leaders = JSON.parse(fs.readFileSync(filePath, "utf8")).leaders;
    return makeTable(label, leaders);
  });

  return [
    beginMarker,
    "## Leader Audio Index",
    "",
    "These links are generated from the current leader voice manifests.",
    "They become live once `tools/elevenlabs-mcp` is configured and `npm run generate:leader-tts` has written clip files into `sound/voices/<leaderKey>/`.",
    "GitHub does not provide reliable inline README audio players, so this section uses direct clip links instead of embedded press-to-play controls.",
    "",
    ...sections,
    endMarker
  ].join("\n");
}

const readme = fs.readFileSync(readmePath, "utf8");
const generatedSection = buildSection();

let nextReadme;

if (readme.includes(beginMarker) && readme.includes(endMarker)) {
  const replacePattern = new RegExp(`${beginMarker}[\\s\\S]*?${endMarker}`);
  nextReadme = readme.replace(replacePattern, generatedSection);
} else {
  const anchor = "## Playable Nation Reference";
  if (!readme.includes(anchor)) {
    throw new Error("README anchor not found.");
  }
  nextReadme = readme.replace(anchor, `${generatedSection}\n\n${anchor}`);
}

fs.writeFileSync(readmePath, nextReadme);
console.log("Updated README audio index.");