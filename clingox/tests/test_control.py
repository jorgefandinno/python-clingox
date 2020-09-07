import unittest
from pprint import pprint

import clingo
from clingo import Control, Function, Number
from clingo.ast import ASTType, Program, ShowSignature

from ..control import ClingoOutputAtom, ClingoProject, ClingoRule, ClingoWeightRule, Controlx


a  = clingo.Function('a', [], True)
b  = clingo.Function('b', [], True)
c  = clingo.Function('c', [], True)
d  = clingo.Function('d', [], True)
e  = clingo.Function('e', [], True)
f  = clingo.Function('f', [], True)

class Test(unittest.TestCase):

    def setUp(self):
        self.control = Controlx(Control(message_limit=0))  

    def test_ground_program(self):
        program = """
        {a}.
        {b}.
        c :- a.
        #project c.
        """
        ground_program = [
            ClingoRule(choice=True,  head=[1], body=[]),
            ClingoRule(choice=False, head=[2], body=[1]),
            ClingoProject(atoms=[2]),
            ClingoRule(choice=True, head=[3], body=[]),
            ClingoOutputAtom(symbol=a, atom=1),
            ClingoOutputAtom(symbol=b, atom=3),
            ClingoOutputAtom(symbol=c, atom=2)
        ]
        ground_program.sort()
        
        self.control.add("base", [], program)
        self.control.ground([("base", [])])
        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)


    def test_pretty_ground_program(self):
        program = """
        {a}.
        {b}.
        c :- a.
        #project c.
        """
        self.control.add("base", [], program)
        self.control.ground([("base", [])])
        self.assertEqual(str(self.control.ground_program).replace(' ','').replace('\n',''), program.replace(' ','').replace('\n',''))


    def test_ground_program_add(self):
        program = """
        {a}.
        {b}.
        c :- a.
        #project c.
        """
        ground_program = [
            ClingoRule(choice=True,  head=[1], body=[]),
            ClingoRule(choice=False, head=[2], body=[1]),
            ClingoProject(atoms=[2]),
            ClingoRule(choice=True, head=[3], body=[]),
            ClingoRule(choice=False, head=[4], body=[1]),
            ClingoOutputAtom(symbol=a, atom=1),
            ClingoOutputAtom(symbol=b, atom=3),
            ClingoOutputAtom(symbol=c, atom=2)
        ]
        ground_program.sort()

        self.control.add("base", [], program)
        self.control.ground([("base", [])])
        with self.control.backend() as backend:
            backend.add_rule([4], [1], False)
        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)


    def test_pertty_ground_program_add(self):
        program = """
        {a}.
        {b}.
        c :- a.
        #project c.
        """      

        self.control.add("base", [], program)
        self.control.ground([("base", [])])
        with self.control.backend() as backend:
            backend.add_rule([4], [1], False)
        pretty_program = """
        {a}.
        {b}.
        c :- a.
        x_4 :- a.
        #project c.
        """     
        self.assertEqual(str(self.control.ground_program).replace(' ','').replace('\n',''), pretty_program.replace(' ','').replace('\n',''))


    def test_ground_program_fact(self):
        program = """
        {a}.
        {b}.
        c :- a.
        #project c.
        """
        ground_program = [
            ClingoRule(choice=True,  head=[1], body=[]),
            ClingoRule(choice=False, head=[2], body=[1]),
            ClingoProject(atoms=[2]),
            ClingoRule(choice=True, head=[3], body=[]),
            ClingoRule(choice=False, head=[4], body=[]),
            ClingoOutputAtom(symbol=a, atom=1),
            ClingoOutputAtom(symbol=b, atom=3),
            ClingoOutputAtom(symbol=c, atom=2)
        ]
        ground_program.sort()

        self.control.add("base", [], program)
        self.control.ground([("base", [])])
        with self.control.backend() as backend:
            backend.add_rule([4], [], False)
        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)


    def test_weight_rule(self):
        program = """
            {a}.
            :- not a.
            {b}.
            c :- #sum{1:a; 2:b} >= 3.
        """
        ground_program = [
            ClingoRule(choice=True, head=[1], body=[], order=1),
            ClingoRule(choice=True, head=[2], body=[], order=1),
            ClingoWeightRule(choice=False, head=[3], body=[(1, 1), (2, 2)], lower=3),
            ClingoRule(choice=False, head=[4], body=[3], order=1),
            ClingoRule(choice=False, head=[], body=[-1], order=1),
            ClingoOutputAtom(symbol=a, atom=1, order=0),
            ClingoOutputAtom(symbol=b, atom=2, order=0),
            ClingoOutputAtom(symbol=c, atom=4, order=0)
        ]
        ground_program.sort()
        
        self.control.configuration.solve.project = "auto,3"
        self.control.configuration.solve.models  = 0

        self.control.add("base", [], program)
        self.control.ground([("base", [])])
        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)

    def test_ground_program_with_parameters(self):
        self.control.add("p", ["t"], "q(t).")
        ground_program = [
            ClingoOutputAtom(symbol=Function("q",[Number(1)], True), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("q",[Number(2)], True), atom=0, order=0),
            ClingoRule(choice=False, head=[1], body=[], order=1),
            ClingoRule(choice=False, head=[2], body=[], order=1)
        ]
        ground_program.sort()

        parts = []
        parts.append(("p", [1]))
        parts.append(("p", [2]))
        self.control.ground(parts)
        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)

    def test_ground_program_with_parameters_and_builder(self):
        program = """
            #program p(t).
            q(t).
            """
        parsed_program = [
            "#program base.",
            "#program p(t).",
            "q(t)."
        ]
        ground_program = [
            ClingoOutputAtom(symbol=Function("q",[Number(1)], True), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("q",[Number(2)], True), atom=0, order=0),
            ClingoRule(choice=False, head=[1], body=[], order=1),
            ClingoRule(choice=False, head=[2], body=[], order=1)
        ]

        parsed_program.sort()
        ground_program.sort()

        with self.control.builder() as builder:
            clingo.parse_program(program, builder.add)       

        self.assertEqual(sorted(map(str,self.control.parsed_program)), parsed_program)

        parts = []
        parts.append(("p", [1]))
        parts.append(("p", [2]))
        self.control.ground(parts)

        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)


    def test_ground_program_with_parameters_and_builder2(self):
        program = """
            #program base(t).
            q(t).
            """
        parsed_program = [
            "#program base.",
            "#program base(t).",
            "q(t)."
        ]
        ground_program = [
            ClingoOutputAtom(symbol=Function("q",[Number(1)], True), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("q",[Number(2)], True), atom=0, order=0),
            ClingoRule(choice=False, head=[1], body=[], order=1),
            ClingoRule(choice=False, head=[2], body=[], order=1)
        ]

        parsed_program.sort()
        ground_program.sort()

        with self.control.builder() as builder:
            clingo.parse_program(program, builder.add)       

        self.assertEqual(sorted(map(str,self.control.parsed_program)), parsed_program)

        parts = []
        parts.append(("base", [1]))
        parts.append(("base", [2]))
        self.control.ground(parts)

        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)

    def test_ground_with_parameters2(self):
        program = """
            a.
            b(n..m).
        """
        ground_program = [
            ClingoOutputAtom(symbol=a, atom=0, order=0),
            ClingoOutputAtom(symbol=Function("b", [Number(1)], True), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("b", [Number(2)], True), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("b", [Number(3)], True), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("b", [Number(11)], True), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("b", [Number(12)], True), atom=0, order=0),
            ClingoRule(choice=False, head=[1], body=[], order=1),
            ClingoRule(choice=False, head=[2], body=[], order=1),
            ClingoRule(choice=False, head=[3], body=[], order=1),
            ClingoRule(choice=False, head=[4], body=[], order=1),
            ClingoRule(choice=False, head=[5], body=[], order=1),
            ClingoRule(choice=False, head=[6], body=[], order=1)
        ]
        ground_program.sort()
        self.control.add("base", ["n", "m"], program)

        parts = []
        parts.append(("base", [1,3]))
        parts.append(("base", [11,12]))
        self.control.ground(parts)
        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)


    def test_ground_with_parameters3(self):
        self.control.add("p", ["t"], "q(t).")
        self.control.add("p", ["s", "t"], "q(t). r(s).")
        ground_program = [
            ClingoOutputAtom(symbol=Function("r",[Number(1)], True), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("q",[Number(2)], True), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("q",[Number(5)], True), atom=0, order=0),
            ClingoRule(choice=False, head=[1], body=[], order=1),
            ClingoRule(choice=False, head=[2], body=[], order=1),
            ClingoRule(choice=False, head=[3], body=[], order=1)
        ]
        ground_program.sort()

        parts = []
        parts.append(("p", [1,5]))
        parts.append(("p", [2]))
        self.control.ground(parts)
        # pprint(sorted(self.control.ground_program.objects))
        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)

    def test_01(self):
        program = """
            u_b :- k_not_u_a.
            not_u_a :- not u_a.
            {k_not_u_a} :- not_u_a.
            """
        ground_program = [
            ClingoOutputAtom(symbol=Function("k_not_u_a",[]), atom=2, order=0),
            ClingoOutputAtom(symbol=Function("not_u_a",[]), atom=0, order=0),
            ClingoOutputAtom(symbol=Function("u_b",[]), atom=3, order=0),
            ClingoRule(choice=False, head=[1], body=[], order=1),
            ClingoRule(choice=False, head=[3], body=[2], order=1),
            ClingoRule(choice=True, head=[2], body=[], order=1)
        ]
        ground_program.sort()
        
        self.control.configuration.solve.project = "auto,3"
        self.control.configuration.solve.models  = 0

        self.control.add("base", [], program)
        self.control.ground([("base", [])])
        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)


    def test_show01(self):
        program = """
            {a}.
            {b}.
            #show b/0.
            """
        ground_program = [
            ClingoOutputAtom(symbol=b, atom=1, order=0),
            ClingoRule(choice=True, head=[1], body=[], order=1),
            ClingoRule(choice=True, head=[2], body=[], order=1)
        ]
        ground_program.sort()
        
        self.control.configuration.solve.project = "auto,3"
        self.control.configuration.solve.models  = 0

        self.control.add("base", [], program)
        self.control.ground([("base", [])])
        self.assertEqual(sorted(self.control.ground_program.objects), ground_program)


    def test_show02(self):
        program = """
            #show a/0.
            """
        parsed_program = [
            Program(    # #program base.
                location = {'begin': {'filename': '<string>', 'line': 1, 'column': 1}, 'end': {'filename': '<string>', 'line': 1, 'column': 1}},
                name = 'base',
                parameters = []
                ),
            ShowSignature(    # #show a/0.
                location = {'begin': {'filename': '<string>', 'line': 2, 'column': 13}, 'end': {'filename': '<string>', 'line': 2, 'column': 23}},
                name = 'a',
                arity = 0,
                positive = True,
                csp = False
            )]
        self.control.add_program(program)       
        self.assertEqual(self.control.parsed_program, parsed_program)


    def test_show02b(self):
        program = """
            #show -a/0.
            """
        parsed_program = [
            Program(    # #program base.
                location = {'begin': {'filename': '<string>', 'line': 1, 'column': 1}, 'end': {'filename': '<string>', 'line': 1, 'column': 1}},
                name = 'base',
                parameters = []
                ),
            ShowSignature(    # #show a/0.
                location = {'begin': {'filename': '<string>', 'line': 2, 'column': 13}, 'end': {'filename': '<string>', 'line': 2, 'column': 23}},
                name = 'a',
                arity = 0,
                positive = False,
                csp = False
            )]
        self.control.add_program(program)
        self.assertEqual(self.control.parsed_program, parsed_program)
