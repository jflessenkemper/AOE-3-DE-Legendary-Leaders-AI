# Dutch + Napoleon vs Russia + Egyptians Templates

Capture these screenshots from the exact lobby layout you want to reuse:

- `single_player_button.png`
- `skirmish_button.png`
- `player1_civ_dropdown.png`
- `player2_civ_dropdown.png`
- `player3_civ_dropdown.png`
- `player4_civ_dropdown.png`
- `civ_dutch.png`
- `civ_napoleonic_france.png`
- `civ_russia.png`
- `civ_egyptians.png`
- `player2_team_dropdown.png`
- `player3_team_dropdown.png`
- `player4_team_dropdown.png`
- `team_1_option.png`
- `team_2_option.png`
- `map_dropdown.png`
- `map_legendary_leaders_test.png`
- `start_game_button.png`

Capture guidance:

- Crop tightly around the clickable label or button, not the whole screen.
- Re-capture if the UI scale, language, or resolution changes.
- For civ entries, capture the list item as it appears in the dropdown, including enough unique text or icon detail to avoid false matches.
- For team options, capture the option row after opening the dropdown.

Example capture command:

```bash
. .venv/bin/activate
python tools/aoe3_automation/aoe3_ui_automation.py capture-reference tools/aoe3_automation/templates/dutch_napoleon_vs_russia_egypt/example.png
```

Run the completed flow with:

```bash
. .venv/bin/activate
python tools/aoe3_automation/aoe3_ui_automation.py run-flow tools/aoe3_automation/flows/dutch_napoleon_vs_russia_egypt_skirmish.json
```