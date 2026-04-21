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

**Legendary Leaders AI** is a standalone Age of Empires III: Definitive Edition mod that combines the base civilizations with the playable revolution roster. Each nation is mapped to a themed leader personality and a clear battlefield identity.

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

