<p align="center">
	<img src="resources/images/legendary_leaders_ai_banner.png" alt="Legendary Leaders AI banner" width="100%">
</p>

<p align="center">
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/validation-suite.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/validation-suite.yml/badge.svg" alt="Validation Suite"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/validator-tests.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/validator-tests.yml/badge.svg" alt="Validator Tests"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/package-validation.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/package-validation.yml/badge.svg" alt="Package Validation"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/civ-homecity-validation.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/civ-homecity-validation.yml/badge.svg" alt="Civ HomeCity Validation"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/civ-crossref-validation.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/civ-crossref-validation.yml/badge.svg" alt="Civ Crossref Validation"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/xml-malformation-check.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/xml-malformation-check.yml/badge.svg" alt="XML Malformation Check"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/stringtable-validation.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/stringtable-validation.yml/badge.svg" alt="StringTable Validation"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/proto-validation.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/proto-validation.yml/badge.svg" alt="Proto Validation"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/techtree-validation.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/techtree-validation.yml/badge.svg" alt="TechTree Validation"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/xs-validation.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/xs-validation.yml/badge.svg" alt="XS Validation"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/homecity-card-validation.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/homecity-card-validation.yml/badge.svg" alt="Homecity Card Validation"></a>
	<a href="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/civmods-ui-validation.yml"><img src="https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/actions/workflows/civmods-ui-validation.yml/badge.svg" alt="Civ UI Validation"></a>
</p>

<table>
<tr>
<td width="70%" valign="middle">

**Legendary Leaders AI** is a standalone Age of Empires III: Definitive Edition mod that combines the base civilizations with the playable revolution roster. Each nation is mapped to a themed leader personality and a clear battlefield identity.

</td>
<td width="30%" align="right" valign="middle">

<a href="https://jflessenkemper.github.io/AOE-3-DE-Legendary-Leaders-AI/">
  <img src="https://img.shields.io/badge/%F0%9F%8F%B0%20Browse%20All%2048%20Nations-1f6feb?style=for-the-badge&logoColor=white" alt="Browse All 48 Nations">
</a>

</td>
</tr>
</table>

## 🏳️ Elite Units and AI Rout

Elite units are chosen case by case for each nation and do not auto-rout. Only AI-controlled non-elite land units are eligible to rout, and they do so at 25% health or below when enemy pressure is present and no friendly elite support is nearby. Player-controlled units keep manual control.

- AI elite units do not auto-rout.
- Only AI-controlled non-elite land units auto-rout.
- The rout threshold is 25% health.
- Nearby friendly elite units block rout.

## 🧭 Leader Escort and Attack Doctrine

Each AI now treats its explorer as the battlefield leader instead of a disposable scout. 

The army tries to keep a living screen around that leader, and different nations decide battles in different ways.

**In short**: some nations win by crushing the line, others look for a leader-kill opening, but all of them now guard their own leader far more carefully.

---

## 📦 Install (for players)

1. Download the latest release zip from the [GitHub Releases page](https://github.com/jflessenkemper/AOE-3-DE-Legendary-Leaders-AI/releases) (or the Steam Workshop subscription once it's live).
2. Extract into your **local mods** folder:
   - **Windows:** `%USERPROFILE%\Games\Age of Empires 3 DE\<steamID>\mods\local\Legendary Leaders AI\`
   - **Linux/Proton:** `~/.local/share/Steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/<steamID>/mods/local/Legendary Leaders AI/`
3. Launch AoE3 DE → **Tools → Mods** → enable **Legendary Leaders AI** → restart game.
4. Pick any civ in Skirmish / Multiplayer lobby — the AI auto-assigns the mod-intended leader (Duke of Wellington for British, Catherine the Great for Russians, etc.) and plays per the HTML reference's doctrine.

**Multiplayer note:** this is intended as a host-only mod. All players in a match should have the same version installed to avoid desyncs.

---

## 🧠 What the mod actually does

- **48 distinct civilizations**: the 22 base civs (re-skinned with historically-accurate leaders) + 26 revolution-era civs promoted to top-level pickable nations (Napoleon, Revolutionary France, Americans, Chileans, Texians, Finns, Barbary States, etc.).
- **Per-leader AI doctrine** via XS scripts — every leader has distinct build-order priorities, military composition, and explorer-escort posture. See the [reference site](https://jflessenkemper.github.io/AOE-3-DE-Legendary-Leaders-AI/) for each civ's doctrine.
- **Curated 25-card Legendary Leaders deck per civ** — AI-authored to match each leader's playstyle (aggressive / defensive / economic / naval).
- **Legendary leader portraits, chat quotes, and name overrides** shown in-match for every civ.
- **Revolutions disabled on standard civs** — since the 26 revolution nations are already pickable as top-level civs, base civs don't offer the old revolution options at age-up.

---

## ⚠️ Known cosmetic limitations

These don't affect gameplay; they're UI-side limits of the AoE3 DE mod engine:

- **Lobby slot thumbnail portraits for base civs** still show the base-game leader (Queen Elizabeth for British, Ivan the Terrible for Russians). The in-match scoreboard, chat portrait, auto-assigned name, and AI doctrine all correctly reflect our legendary leader (Duke of Wellington, Catherine the Great, etc.) — only the small lobby thumbnail is stuck.
- **Deck Builder for base civs** shows the base-game decks (Beginner / Land / Naval / Tycoon / Treaty). The 26 revolution civs correctly show the Legendary Leaders deck. Engine-level limitation for overriding packed homecity data.
- **"MY DECK" label** stays that way in the Deck Builder (engine stores it as a literal in the binary savegame). The deck content inside is our Legendary Leaders 25-card curation.

---

## 📤 Publishing to the Steam Workshop (for maintainers)

1. In-game: **Tools → Mods → Mod Manager**.
2. Select **Legendary Leaders AI** from the Local Mods list.
3. Click **Publish** (or **Upload to Workshop**) — the dialog asks for:
   - **Title:** `Legendary Leaders AI`
   - **Description:** paste the short summary from the top of this README
   - **Tags:** `AI`, `Civilizations`, `Gameplay`, `Revolutions`
   - **Visibility:** `Public`
   - **Thumbnail:** upload `resources/images/legendary_leaders_ai_banner.png` (or a cropped 512×512 square of it) when asked
4. Accept the Workshop agreement, click Upload, and the mod syncs to your Workshop page.
5. For updates: change the `version` in `modinfo.json`, re-open Mod Manager → Publish → **Update Existing** (keeps the same Workshop item ID, so subscribers get the update automatically).

If you'd rather avoid the in-game flow and upload via CLI, use `steamcmd` with the `workshop_build_item` command and a VDF file referencing the mod folder — but the in-game path is simpler for first-time publishes.

