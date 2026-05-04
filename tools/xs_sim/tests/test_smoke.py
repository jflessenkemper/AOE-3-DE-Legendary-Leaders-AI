"""End-to-end smoke tests. Run with: python3 -m unittest tools.xs_sim.tests.test_smoke"""
import unittest
from pathlib import Path

from tools.xs_sim.lexer import tokenize
from tools.xs_sim.parser import parse
from tools.xs_sim.interpreter import Interpreter
from tools.xs_sim.gamestate import scenario_open_age2

REPO = Path(__file__).resolve().parents[3]


class TestLexer(unittest.TestCase):
    def test_basics(self):
        toks = tokenize("int x = 5; // comment\nfloat y = 3.14;")
        kinds = [t.kind for t in toks if t.kind != "eof"]
        self.assertEqual(kinds, ["kw", "id", "op", "int", "op",
                                 "kw", "id", "op", "float", "op"])

    def test_ternary(self):
        toks = tokenize("a ? 1 : 2")
        ops = [t.value for t in toks if t.kind == "op"]
        self.assertIn("?", ops); self.assertIn(":", ops)


class TestParser(unittest.TestCase):
    def test_rule(self):
        prog = parse("rule r1 inactive minInterval 30 { }")
        self.assertEqual(len(prog.items), 1)
        self.assertEqual(prog.items[0].name, "r1")
        self.assertFalse(prog.items[0].active)
        self.assertEqual(prog.items[0].min_interval, 30)

    def test_c_style_for(self):
        prog = parse("void f() { for (int i = 0; i < 10; i++) { } }")
        # Should parse without error; outer item is FuncDef.
        self.assertEqual(prog.items[0].name, "f")

    def test_switch(self):
        prog = parse("void f() { switch (x) { case 1: break; default: break; } }")
        self.assertEqual(prog.items[0].name, "f")

    def test_ternary_expr(self):
        prog = parse("int g = 1 > 0 ? 5 : 6;")
        self.assertEqual(prog.items[0].name, "g")

    def test_all_leader_files_parse(self):
        leaders = sorted((REPO / "game" / "ai" / "leaders").glob("leader_*.xs"))
        self.assertGreater(len(leaders), 20, "expected ≥20 leader files")
        for f in leaders:
            with self.subTest(leader=f.name):
                parse(f.read_text(), str(f))


class TestInterpreter(unittest.TestCase):
    def test_basic_arith(self):
        i = Interpreter()
        i.load_source("int g = 2 + 3 * 4;")
        self.assertEqual(i.globals["g"], 14)

    def test_function_call(self):
        i = Interpreter()
        i.load_source("int add(int a, int b) { return a + b; } int g = add(2, 5);")
        self.assertEqual(i.globals["g"], 7)

    def test_ternary(self):
        i = Interpreter()
        i.load_source("int g = (1 < 2) ? 10 : 20;")
        self.assertEqual(i.globals["g"], 10)

    def test_rule_fires_at_interval(self):
        i = Interpreter()
        i.load_source(
            "int counter = 0;"
            "rule r active minInterval 5 { counter = counter + 1; }"
        )
        i.run(20.0, dt=1.0)
        # Fires at t=5,10,15,20 (last_fire starts at -inf, so first fire at t=5
        # since dt=1 increments time before evaluating the threshold).
        self.assertGreaterEqual(i.globals["counter"], 3)

    def test_napoleon_init_sets_doctrine(self):
        i = Interpreter()
        i.load_file(REPO / "game" / "ai" / "leaders" / "leader_napoleon.xs")
        i.call_init("initLeaderNapoleon")
        self.assertEqual(i.globals.get("btRushBoom"), 0.1)
        self.assertEqual(i.globals.get("btBiasTrade"), -0.4)   # Continental System
        self.assertTrue(i.globals.get("gNapoleonRulesEnabled"))

    def test_xs_disable_self(self):
        i = Interpreter()
        i.load_source(
            "int counter = 0;"
            "rule r active minInterval 1 { counter = counter + 1; xsDisableSelf(); }"
        )
        i.run(10.0, dt=1.0)
        self.assertEqual(i.globals["counter"], 1)


if __name__ == "__main__":
    unittest.main()
