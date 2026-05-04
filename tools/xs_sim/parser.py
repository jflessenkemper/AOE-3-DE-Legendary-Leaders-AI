"""Recursive-descent parser for XS.

XS grammar covered:
  Program      := (Include | VarDecl | FuncDef | RuleDef)*
  VarDecl      := ['const'|'static'|'extern']* Type Ident ['=' Expr] ';'
  FuncDef      := Type Ident '(' Params ')' Block
  Params       := (Type Ident ['=' Expr] (',' ...)*)?
  RuleDef      := 'rule' Ident RuleAttrs Block
  RuleAttrs    := ('active'|'inactive'|'minInterval' Num|'maxInterval' Num
                  |'highFrequency'|'runImmediately'|'priority' Num
                  |'group' Ident)*
  Block        := '{' Stmt* '}'
  Stmt         := VarDecl | If | While | For | Return | Break | Continue
                 | Block | ExprStmt
  ExprStmt     := Expr ';'

Expression precedence (low → high): assign, ||, &&, == !=, < <= > >=,
+ -, * / %, unary !-, postfix call/index, primary.
"""
from __future__ import annotations
from typing import Optional

from .lexer import Token
from . import ast_nodes as A


TYPE_KWS = {"void", "int", "float", "bool", "string", "vector"}


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list[Token], filename: str = "<src>"):
        self.toks = tokens
        self.pos = 0
        self.filename = filename

    # ---- token helpers ----

    def peek(self, k: int = 0) -> Token:
        return self.toks[min(self.pos + k, len(self.toks) - 1)]

    def eat(self) -> Token:
        t = self.toks[self.pos]
        if self.pos < len(self.toks) - 1:
            self.pos += 1
        return t

    def check(self, kind: str, value: Optional[str] = None) -> bool:
        t = self.peek()
        if t.kind != kind:
            return False
        if value is not None and t.value != value:
            return False
        return True

    def match(self, kind: str, value: Optional[str] = None) -> Optional[Token]:
        if self.check(kind, value):
            return self.eat()
        return None

    def expect(self, kind: str, value: Optional[str] = None) -> Token:
        t = self.peek()
        if not self.check(kind, value):
            want = f"{kind}={value!r}" if value else kind
            raise ParseError(
                f"{self.filename}:{t.line}:{t.col} expected {want}, "
                f"got {t.kind}={t.value!r}"
            )
        return self.eat()

    # ---- top level ----

    def parse_program(self) -> A.Program:
        items: list = []
        while not self.check("eof"):
            items.append(self._parse_top())
        return A.Program(items=items)

    def _parse_top(self):
        t = self.peek()
        if t.kind == "include":
            self.eat()
            return A.Include(path=t.value, line=t.line, col=t.col)
        if self.check("kw", "rule"):
            return self._parse_rule()

        # Skip storage-class keywords (const/static/extern) — purely advisory
        # for the simulator. We treat them all as plain decls.
        is_const = False
        while self.check("kw", "const") or self.check("kw", "static") or self.check("kw", "extern"):
            kw = self.eat()
            if kw.value == "const":
                is_const = True

        # Type keyword is required for top-level decls (var or func).
        if not (t.kind == "kw" and self.peek().value in TYPE_KWS):
            raise ParseError(
                f"{self.filename}:{t.line}:{t.col} expected declaration, "
                f"got {t.kind}={t.value!r}"
            )
        type_tok = self.eat()

        # Function-pointer type:  bool(int, int) name = init;
        # If `(` immediately follows the type keyword (no ident in between),
        # this is a fn-pointer var decl. Skip the type list — we don't
        # typecheck pointer signatures.
        if self.check("op", "("):
            self.expect("op", "(")
            depth = 1
            while depth > 0:
                t = self.eat()
                if t.kind == "op" and t.value == "(": depth += 1
                elif t.kind == "op" and t.value == ")": depth -= 1
            name_tok = self.expect("id")
            init = None
            if self.match("op", "="):
                init = self._parse_expr()
            self.expect("op", ";")
            return A.VarDecl(typ=type_tok.value, name=name_tok.value, init=init,
                             is_const=is_const, line=type_tok.line, col=type_tok.col)

        name_tok = self.expect("id")
        if self.check("op", "("):
            return self._parse_func_def_after_header(type_tok, name_tok)
        # Variable decl
        init: Optional[A.Expr] = None
        if self.match("op", "="):
            init = self._parse_expr()
        self.expect("op", ";")
        return A.VarDecl(
            typ=type_tok.value, name=name_tok.value, init=init,
            is_const=is_const, line=type_tok.line, col=type_tok.col,
        )

    def _parse_func_def_after_header(self, type_tok: Token, name_tok: Token) -> A.FuncDef:
        self.expect("op", "(")
        params: list[A.Param] = []
        if not self.check("op", ")"):
            params.append(self._parse_param())
            while self.match("op", ","):
                params.append(self._parse_param())
        self.expect("op", ")")
        body = self._parse_block()
        return A.FuncDef(
            return_type=type_tok.value, name=name_tok.value,
            params=params, body=body,
            line=type_tok.line, col=type_tok.col,
        )

    def _parse_param(self) -> A.Param:
        # Special case: "void" alone in param list = no params; but caller
        # already short-circuits on ')'. We still accept `void` typed param.
        t = self.peek()
        if t.kind != "kw" or t.value not in TYPE_KWS:
            raise ParseError(
                f"{self.filename}:{t.line}:{t.col} expected param type, got {t.value!r}"
            )
        typ = self.eat().value
        # Allow `void` with no name (legacy XS habit).
        if typ == "void" and not self.check("id"):
            return A.Param(typ="void", name="")
        name = self.expect("id").value
        default = None
        if self.match("op", "="):
            default = self._parse_expr()
        return A.Param(typ=typ, name=name, default=default)

    def _parse_rule(self) -> A.RuleDef:
        kw = self.expect("kw", "rule")
        name = self.expect("id").value
        rd = A.RuleDef(name=name, line=kw.line, col=kw.col)
        # Attributes appear in any order until '{'
        while not self.check("op", "{"):
            t = self.peek()
            if self.match("kw", "active"):
                rd.active = True
            elif self.match("kw", "inactive"):
                rd.active = False
            elif self.match("kw", "minInterval"):
                rd.min_interval = self._parse_number()
            elif self.match("kw", "maxInterval"):
                rd.max_interval = self._parse_number()
            elif self.match("kw", "highFrequency"):
                rd.high_frequency = True
            elif self.match("kw", "runImmediately"):
                rd.run_immediately = True
            elif self.match("kw", "priority"):
                rd.priority = int(self._parse_number())
            elif self.match("kw", "group"):
                rd.group = self.expect("id").value
            else:
                raise ParseError(
                    f"{self.filename}:{t.line}:{t.col} unexpected rule attr {t.value!r}"
                )
        rd.body = self._parse_block()
        return rd

    def _parse_number(self) -> float:
        t = self.eat()
        if t.kind == "int":
            return float(int(t.value))
        if t.kind == "float":
            return float(t.value)
        raise ParseError(f"{self.filename}:{t.line}:{t.col} expected number, got {t.value!r}")

    # ---- statements ----

    def _parse_block(self) -> A.Block:
        lb = self.expect("op", "{")
        stmts: list = []
        while not self.check("op", "}"):
            stmts.append(self._parse_stmt())
        self.expect("op", "}")
        return A.Block(stmts=stmts, line=lb.line, col=lb.col)

    def _parse_stmt(self):
        t = self.peek()

        # Block
        if t.kind == "op" and t.value == "{":
            return self._parse_block()

        # Local var decl: type ident [= expr] ;
        if t.kind == "kw" and t.value in TYPE_KWS and self.peek(1).kind == "id":
            type_tok = self.eat()
            name_tok = self.expect("id")
            init = None
            if self.match("op", "="):
                init = self._parse_expr()
            self.expect("op", ";")
            return A.VarDecl(
                typ=type_tok.value, name=name_tok.value, init=init,
                line=type_tok.line, col=type_tok.col,
            )

        # const/static local
        if t.kind == "kw" and t.value in ("const", "static", "extern"):
            self.eat()
            return self._parse_stmt()

        if self.match("kw", "if"):
            return self._parse_if(t)
        if self.match("kw", "while"):
            return self._parse_while(t)
        if self.match("kw", "for"):
            return self._parse_for(t)
        if self.match("kw", "switch"):
            return self._parse_switch(t)
        if self.match("kw", "return"):
            ret = A.Return(line=t.line, col=t.col)
            if not self.check("op", ";"):
                ret.value = self._parse_expr()
            self.expect("op", ";")
            return ret
        if self.match("kw", "break"):
            self.expect("op", ";")
            return A.Break(line=t.line, col=t.col)
        if self.match("kw", "continue"):
            self.expect("op", ";")
            return A.Continue(line=t.line, col=t.col)

        # Expression statement
        e = self._parse_expr()
        self.expect("op", ";")
        return A.ExprStmt(expr=e, line=t.line, col=t.col)

    def _parse_if(self, kw: Token) -> A.If:
        self.expect("op", "(")
        cond = self._parse_expr()
        self.expect("op", ")")
        then = self._wrap_block(self._parse_stmt())
        els = None
        if self.match("kw", "else"):
            els = self._wrap_block(self._parse_stmt())
        return A.If(cond=cond, then=then, els=els, line=kw.line, col=kw.col)

    def _parse_while(self, kw: Token) -> A.While:
        self.expect("op", "(")
        cond = self._parse_expr()
        self.expect("op", ")")
        body = self._wrap_block(self._parse_stmt())
        return A.While(cond=cond, body=body, line=kw.line, col=kw.col)

    def _parse_for(self, kw: Token) -> A.For:
        """Two forms exist in this codebase:
            XS-classic:  for (i = 0; < 5)        { ... }
            C-style:     for (int i = 0; i < n; i++) { ... }
        """
        self.expect("op", "(")

        # Detect C-style: starts with type kw, OR has 2 semicolons in the header.
        is_c_style = (self.peek().kind == "kw" and self.peek().value in TYPE_KWS)
        if not is_c_style:
            # Lookahead: scan tokens until matching ')' counting ';'.
            depth = 0; semis = 0; j = self.pos
            while j < len(self.toks):
                tk = self.toks[j]
                if tk.kind == "op":
                    if tk.value == "(":
                        depth += 1
                    elif tk.value == ")":
                        if depth == 0:
                            break
                        depth -= 1
                    elif tk.value == ";" and depth == 0:
                        semis += 1
                j += 1
            is_c_style = semis >= 2

        if is_c_style:
            # init
            init_stmt = None
            if not self.check("op", ";"):
                if self.peek().kind == "kw" and self.peek().value in TYPE_KWS:
                    type_tok = self.eat()
                    name_tok = self.expect("id")
                    init_e = None
                    if self.match("op", "="):
                        init_e = self._parse_expr()
                    init_stmt = A.VarDecl(typ=type_tok.value, name=name_tok.value,
                                          init=init_e, line=type_tok.line, col=type_tok.col)
                else:
                    init_stmt = A.ExprStmt(expr=self._parse_expr(), line=kw.line, col=kw.col)
            self.expect("op", ";")
            cond = None if self.check("op", ";") else self._parse_expr()
            self.expect("op", ";")
            step = None if self.check("op", ")") else self._parse_expr()
            self.expect("op", ")")
            body = self._wrap_block(self._parse_stmt())
            return A.CForLoop(init=init_stmt, cond=cond, step=step, body=body,
                              line=kw.line, col=kw.col)

        # XS-classic
        var = self.expect("id").value
        self.expect("op", "=")
        start = self._parse_expr()
        self.expect("op", ";")
        if any(self.check("op", o) for o in ("<", "<=", ">", ">=")):
            self.eat()
        end = self._parse_expr()
        self.expect("op", ")")
        body = self._wrap_block(self._parse_stmt())
        return A.For(var=var, start=start, end=end, body=body, line=kw.line, col=kw.col)

    def _parse_switch(self, kw: Token) -> A.Switch:
        self.expect("op", "(")
        expr = self._parse_expr()
        self.expect("op", ")")
        self.expect("op", "{")
        cases: list[A.SwitchCase] = []
        while not self.check("op", "}"):
            if self.match("kw", "case"):
                val = self._parse_expr()
                self.expect("op", ":")
                body = self._parse_case_body()
                cases.append(A.SwitchCase(value=val, body=body, line=kw.line, col=kw.col))
            elif self.match("kw", "default"):
                self.expect("op", ":")
                body = self._parse_case_body()
                cases.append(A.SwitchCase(value=None, body=body, line=kw.line, col=kw.col))
            else:
                t = self.peek()
                raise ParseError(f"{self.filename}:{t.line}:{t.col} expected case/default")
        self.expect("op", "}")
        return A.Switch(expr=expr, cases=cases, line=kw.line, col=kw.col)

    def _parse_case_body(self) -> A.Block:
        # Body is either a single block `{...}` or stmts up to next case/default/}.
        if self.check("op", "{"):
            return self._parse_block()
        stmts: list = []
        while not (self.check("kw", "case") or self.check("kw", "default")
                   or self.check("op", "}")):
            stmts.append(self._parse_stmt())
        return A.Block(stmts=stmts)

    @staticmethod
    def _wrap_block(stmt) -> A.Block:
        if isinstance(stmt, A.Block):
            return stmt
        return A.Block(stmts=[stmt], line=getattr(stmt, "line", 0),
                       col=getattr(stmt, "col", 0))

    # ---- expressions ----

    def _parse_expr(self) -> A.Expr:
        return self._parse_assign()

    def _parse_assign(self) -> A.Expr:
        left = self._parse_ternary()
        for op in ("=", "+=", "-=", "*=", "/=", "%="):
            if self.check("op", op):
                t = self.eat()
                right = self._parse_assign()
                return A.Assign(op=op, target=left, value=right, line=t.line, col=t.col)
        return left

    def _parse_ternary(self) -> A.Expr:
        cond = self._parse_or()
        if self.check("op", "?"):
            t = self.eat()
            then = self._parse_assign()
            self.expect("op", ":")
            els = self._parse_assign()
            return A.Ternary(cond=cond, then=then, els=els, line=t.line, col=t.col)
        return cond

    def _parse_or(self) -> A.Expr:
        left = self._parse_and()
        while self.check("op", "||"):
            t = self.eat()
            right = self._parse_and()
            left = A.Binary(op="||", left=left, right=right, line=t.line, col=t.col)
        return left

    def _parse_and(self) -> A.Expr:
        left = self._parse_bitor()
        while self.check("op", "&&"):
            t = self.eat()
            right = self._parse_bitor()
            left = A.Binary(op="&&", left=left, right=right, line=t.line, col=t.col)
        return left

    def _parse_bitor(self) -> A.Expr:
        left = self._parse_bitxor()
        while self.check("op", "|"):
            t = self.eat()
            right = self._parse_bitxor()
            left = A.Binary(op="|", left=left, right=right, line=t.line, col=t.col)
        return left

    def _parse_bitxor(self) -> A.Expr:
        left = self._parse_bitand()
        while self.check("op", "^"):
            t = self.eat()
            right = self._parse_bitand()
            left = A.Binary(op="^", left=left, right=right, line=t.line, col=t.col)
        return left

    def _parse_bitand(self) -> A.Expr:
        left = self._parse_eq()
        while self.check("op", "&"):
            t = self.eat()
            right = self._parse_eq()
            left = A.Binary(op="&", left=left, right=right, line=t.line, col=t.col)
        return left

    def _parse_eq(self) -> A.Expr:
        left = self._parse_cmp()
        while self.check("op", "==") or self.check("op", "!="):
            t = self.eat()
            right = self._parse_cmp()
            left = A.Binary(op=t.value, left=left, right=right, line=t.line, col=t.col)
        return left

    def _parse_cmp(self) -> A.Expr:
        left = self._parse_add()
        while any(self.check("op", o) for o in ("<", "<=", ">", ">=")):
            t = self.eat()
            right = self._parse_add()
            left = A.Binary(op=t.value, left=left, right=right, line=t.line, col=t.col)
        return left

    def _parse_add(self) -> A.Expr:
        left = self._parse_mul()
        while self.check("op", "+") or self.check("op", "-"):
            t = self.eat()
            right = self._parse_mul()
            left = A.Binary(op=t.value, left=left, right=right, line=t.line, col=t.col)
        return left

    def _parse_mul(self) -> A.Expr:
        left = self._parse_unary()
        while any(self.check("op", o) for o in ("*", "/", "%")):
            t = self.eat()
            right = self._parse_unary()
            left = A.Binary(op=t.value, left=left, right=right, line=t.line, col=t.col)
        return left

    def _parse_unary(self) -> A.Expr:
        if self.check("op", "!") or self.check("op", "-") or self.check("op", "+") or self.check("op", "~"):
            t = self.eat()
            operand = self._parse_unary()
            return A.Unary(op=t.value, operand=operand, line=t.line, col=t.col)
        return self._parse_postfix()

    def _parse_postfix(self) -> A.Expr:
        node = self._parse_primary()
        while True:
            if self.check("op", "["):
                t = self.eat()
                idx = self._parse_expr()
                self.expect("op", "]")
                node = A.Index(target=node, index=idx, line=t.line, col=t.col)
            elif self.check("op", "++") or self.check("op", "--"):
                t = self.eat()
                # postfix ++/-- → desugar to (x = x +/- 1)
                op = "+" if t.value == "++" else "-"
                node = A.Assign(
                    op="=", target=node,
                    value=A.Binary(op=op, left=node,
                                   right=A.IntLit(value=1, line=t.line, col=t.col),
                                   line=t.line, col=t.col),
                    line=t.line, col=t.col,
                )
            else:
                break
        return node

    def _parse_primary(self) -> A.Expr:
        t = self.peek()

        if t.kind == "int":
            self.eat()
            return A.IntLit(value=int(t.value), line=t.line, col=t.col)
        if t.kind == "float":
            self.eat()
            return A.FloatLit(value=float(t.value), line=t.line, col=t.col)
        if t.kind == "str":
            self.eat()
            return A.StrLit(value=t.value, line=t.line, col=t.col)
        if t.kind == "kw" and t.value in ("true", "false"):
            self.eat()
            return A.BoolLit(value=(t.value == "true"), line=t.line, col=t.col)

        # vector(x, y, z)
        if t.kind == "kw" and t.value == "vector":
            self.eat()
            self.expect("op", "(")
            x = self._parse_expr(); self.expect("op", ",")
            y = self._parse_expr(); self.expect("op", ",")
            z = self._parse_expr(); self.expect("op", ")")
            return A.VectorLit(x=x, y=y, z=z, line=t.line, col=t.col)

        # parenthesised
        if t.kind == "op" and t.value == "(":
            self.eat()
            e = self._parse_expr()
            self.expect("op", ")")
            return e

        # identifier — variable or call
        if t.kind == "id":
            self.eat()
            if self.check("op", "("):
                self.eat()
                args: list = []
                if not self.check("op", ")"):
                    args.append(self._parse_expr())
                    while self.match("op", ","):
                        args.append(self._parse_expr())
                self.expect("op", ")")
                return A.Call(name=t.value, args=args, line=t.line, col=t.col)
            return A.Var(name=t.value, line=t.line, col=t.col)

        raise ParseError(
            f"{self.filename}:{t.line}:{t.col} unexpected token {t.kind}={t.value!r} in expression"
        )


def parse(src: str, filename: str = "<src>") -> A.Program:
    from .lexer import tokenize
    return Parser(tokenize(src, filename), filename).parse_program()
