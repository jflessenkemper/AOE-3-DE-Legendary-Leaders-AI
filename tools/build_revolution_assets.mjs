import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = path.resolve(new URL("..", import.meta.url).pathname);
const manifestPaths = [
  path.join(root, "resources", "audio", "standard_leader_manifest.json"),
  path.join(root, "resources", "audio", "revolution_leader_manifest.json")
];
const manifest = {
  leaders: manifestPaths.flatMap((manifestPath) => JSON.parse(fs.readFileSync(manifestPath, "utf8")).leaders)
};

fs.mkdirSync(path.join(root, "art", "ui", "leaders"), { recursive: true });
fs.mkdirSync(path.join(root, "resources", "images", "icons", "singleplayer"), { recursive: true });

const failures = [];

for (const leader of manifest.leaders) {
  const portraitPath = path.join(root, leader.portraitLocalFile);
  const wpfPath = path.join(root, leader.smallPortraitFile);

  try {
    if (!fs.existsSync(portraitPath)) {
      let imageUrl = leader.portraitSourceUrl;

      if (!imageUrl) {
        const html = execFileSync("curl", ["-L", "-s", leader.articleUrl], {
          cwd: root,
          encoding: "utf8",
          maxBuffer: 20 * 1024 * 1024
        });
        const match = html.match(/(?:https:)?\/\/upload\.wikimedia\.org[^\"\s]+/);

        if (!match) {
          throw new Error(`No Wikimedia image found for ${leader.leaderName}`);
        }

        imageUrl = match[0].startsWith("//") ? `https:${match[0]}` : match[0];
      }

      fs.mkdirSync(path.dirname(portraitPath), { recursive: true });
      execFileSync(
        "curl",
        ["-L", "-A", "Mozilla/5.0", "-e", "https://en.wikipedia.org/", "-s", imageUrl, "-o", portraitPath],
        { cwd: root, stdio: "inherit" }
      );
    }

    fs.mkdirSync(path.dirname(wpfPath), { recursive: true });
    execFileSync(
      "ffmpeg",
      [
        "-y",
        "-i",
        portraitPath,
        "-frames:v",
        "1",
        "-update",
        "1",
        "-vf",
        "scale=256:256:force_original_aspect_ratio=decrease,pad=256:256:(ow-iw)/2:(oh-ih)/2:color=0x1a1a1a",
        wpfPath
      ],
      { cwd: root, stdio: "inherit" }
    );
    console.log(`built ${leader.leaderKey}`);
  } catch (error) {
    failures.push({ leader: leader.leaderKey, message: error.message });
  }
}

if (failures.length > 0) {
  console.error(JSON.stringify({ failures }, null, 2));
  process.exitCode = 1;
}