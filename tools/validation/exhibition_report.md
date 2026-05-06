# Exhibition Match Report

**Generated:** 2026-04-21T17:54:01.420461
**Total time:** 930s (15.5m)
**Result:** 0/5 civs passed ✅

## Summary

| Civ | Leader | Rename | Deck | Escort | Ransom | Rout | Suites | Status |
|-----|--------|--------|------|--------|--------|------|--------|--------|
| British | Duke of Wellington | ❌ | ❌ | ❌ | ❌ | ❌ | 0/0 | ❌ ERROR: 'NoneType' object has no attribute 'exis |
| Japanese | Tokugawa Ieyasu | ❌ | ❌ | ❌ | ❌ | ❌ | 0/0 | ❌ ERROR: 'NoneType' object has no attribute 'exis |
| Aztecs | Montezuma II | ❌ | ❌ | ❌ | ❌ | ❌ | 0/0 | ❌ ERROR: 'NoneType' object has no attribute 'exis |
| rvltmodhomecitynapoleon | Napoleon Bonaparte | ❌ | ❌ | ❌ | ❌ | ❌ | 0/0 | ❌ ERROR: 'NoneType' object has no attribute 'exis |
| rvltmodhomecitytexas | Sam Houston | ❌ | ❌ | ❌ | ❌ | ❌ | 0/0 | ❌ ERROR: 'NoneType' object has no attribute 'exis |

## Civs Needing Review

- **British** (homecitybritish): leader name not found, deck not loaded, escort plan never fired, rout plan never fired, ERROR: 'NoneType' object has no attribute 'exists'
- **Japanese** (homecityjapanese): leader name not found, deck not loaded, escort plan never fired, rout plan never fired, ERROR: 'NoneType' object has no attribute 'exists'
- **Aztecs** (homecityxpaztec): leader name not found, deck not loaded, escort plan never fired, rout plan never fired, ERROR: 'NoneType' object has no attribute 'exists'
- **rvltmodhomecitynapoleon** (rvltmodhomecitynapoleon): leader name not found, deck not loaded, escort plan never fired, rout plan never fired, ERROR: 'NoneType' object has no attribute 'exists'
- **rvltmodhomecitytexas** (rvltmodhomecitytexas): leader name not found, deck not loaded, escort plan never fired, rout plan never fired, ERROR: 'NoneType' object has no attribute 'exists'

## Configuration

- Match length: 180s per civ
- Launch method: Automated (steam:// or proton)
- Test opponent: RvltModNapoleonicFrance
- Difficulty: Hard
- Scenario: Legendary Leaders Test

## How to Reproduce

```bash
python3 tools/validation/exhibition_runner.py --dry-run
python3 tools/validation/exhibition_runner.py --match-seconds 180
```

See `tools/validation/EXHIBITION_RUNNER.md` for detailed instructions.