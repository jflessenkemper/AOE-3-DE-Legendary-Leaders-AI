<div align="center" style="margin: 40px 0; padding: 30px; border: 2px solid #6e4f24; background: linear-gradient(135deg, rgba(22,13,4,0.8), rgba(40,25,10,0.8)); border-radius: 8px;">
  <h1 style="font-family: 'Trajan Pro', serif; font-size: 48px; letter-spacing: 0.15em; color: #e9c971; text-shadow: 0 2px 4px rgba(0,0,0,0.8); margin: 20px 0;">A NEW WORLD</h1>
  <p style="color: #d6c896; font-size: 16px; margin: 15px 0;">48 civilizations • Historical leaders • Authentic decks • Unique AI doctrines</p>
</div>

<p align="center">
	<a href="https://github.com/jflessenkemper/AOE-3-DE-A-New-World-DLC/actions/workflows/validation-suite.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-A-New-World-DLC/actions/workflows/validation-suite.yml/badge.svg" alt="Validation Suite"></a>
	<img src="https://img.shields.io/badge/Status-Complete-brightgreen?style=flat-square" alt="Status">
	<img src="https://img.shields.io/badge/Civilizations-48-blue?style=flat-square" alt="Civilizations">
	<img src="https://img.shields.io/badge/Leaders-48-orange?style=flat-square" alt="Leaders">
	<img src="https://img.shields.io/badge/Decks-48-green?style=flat-square" alt="Decks">
	<img src="https://img.shields.io/badge/AI%20Doctrines-48-blueviolet?style=flat-square" alt="AI Doctrines">
	<img src="https://img.shields.io/badge/Version-1.0.0-blue?style=flat-square" alt="Version">
	<img src="https://img.shields.io/github/repo-size/jflessenkemper/AOE-3-DE-A-New-World?style=flat-square" alt="Repo Size">
	<img src="https://img.shields.io/github/license/jflessenkemper/AOE-3-DE-A-New-World-DLC?style=flat-square" alt="License">
	<img src="https://img.shields.io/github/last-commit/jflessenkemper/AOE-3-DE-A-New-World?style=flat-square" alt="Last Commit">
</p>

**A New World** is a comprehensive mod that transforms Age of Empires III: Definitive Edition by unifying all 22 base civilizations with their 26 playable revolutions into one cohesive 48-nation experience. Each civilization is reimagined with a historically-accurate leader personality, a carefully curated 25-card home city deck tailored to that leader's playstyle and era, a uniquely designed AI doctrine with authentic build orders and unit compositions, and historically grounded map placement bias that reflects where each nation actually thrived.

## Quick Start

1. Download the latest release from [Releases](../../releases)
2. Extract into your mods directory:
   - **Windows:** `%USERPROFILE%\Games\Age of Empires 3 DE\<steamID>\mods\local\`
   - **Proton/Linux:** `~/.local/share/Steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/<steamID>/mods/local/`
3. Enable in-game: *Home City → Mods → Local Mods → A New World → Enable*
4. Start a Skirmish — all 48 nations available in the civ picker

> **Note:** Host-only mod. All players must have it installed and enabled.

## Features

- **48 playable civs** — Napoleon, Revolutionary France, Americans, Chileans, Texians, Finns, Barbary, Haitians, and more
- **Leader authenticity** — Elizabeth I for British, Ivan the Terrible for Russians, Toussaint Louverture for Haitians, etc.
- **Curated decks** — 25-card "A New World" decks matched to each leader's playstyle and era
- **Unique AI doctrines** — 48 distinct build orders, unit comps, and explorer tactics in XS
- **Historical map placement** — civs spawn where they belong: British on coasts, Russians upriver, Lakota on plains, etc.
- **Smart leader-escort AI** — explorer positioning and rout mechanics reflect the leader's role
- **Reference site** — [Browse all 48 nations](https://jflessenkemper.github.io/AOE-3-DE-A-New-World-DLC/) with playstyle guides, strategies, and decks

## Repository

| File | Purpose |
|---|---|
| `a_new_world.html` | Interactive reference site (decks, strategies, leader quotes) |
| `data/decks_anw.json` | 25-card "A New World" deck per civ |
| `data/civmods.xml` | Unit balancing, UI labels, and civ metadata |
| `game/ai/anw*.personality` | Per-leader AI doctrine and build orders |
| `data/anwhomecity*.xml` | Homecity deck definitions |

---

**Made with ❤️ for Age of Empires III fans who want authentic, balanced, historically-grounded multiplayer civs.**
