"""xs_sim — standalone interpreter for AoE3 DE XS scripts.

Stdlib-only. Parses XS source, runs rules under a tick-based scheduler,
and resolves kb*/ai* queries against a mock GameState. Intended for
testing AI doctrine compliance without the game engine.
"""
