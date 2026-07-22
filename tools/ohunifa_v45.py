#!/usr/bin/env python3

# ------------------------------------------------------
# IFÁ project import bootstrap
# ------------------------------------------------------

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ------------------------------------------------------

import argparse
import cmd

from parser.parser import parser
from parser.nodes import FunctionNode
from interpreter.interpreter import interpreter
from runtime.backend_manager import backend_manager
from compiler.ast_optimizer import ast_optimizer
from compiler.ir import ir_lowerer
from compiler.rtl_generator import systemverilog_generator
from compiler.diagnostics import format_diagnostic
from runtime.ifa_services_v45 import ifa_services_v45
from runtime.input_entry_v45 import correct_prime_sum, render_correction

class OhunIFAShell(cmd.Cmd):

    intro = """
==========================================================
             OHÙN IFÁ Processor V4.5
==========================================================

Native RMU Computation Engine

Type HELP for commands.
"""

    prompt = "KỌ WỌLÉ > "

    def __init__(self, backend_name="python"):
        super().__init__()

        backend_manager.use(backend_name)
        self.yara_gbobo = False
        self.paste_lines = None
        self.declaration_lines = None
        self.declaration_depth = 0

    # --------------------------------------------------
    # Complete program input
    # --------------------------------------------------

    def precmd(self, line):
        if line.strip():
            print("Ó WỌLÉ")
        return line

    def onecmd(self, line):

        if self.paste_lines is not None:
            if line.strip().upper() in ("OTAN", "END"):
                source = "\n".join(self.paste_lines)
                self.paste_lines = None
                self.prompt = "KỌ WỌLÉ > "

                if not source.strip():
                    print("KÒ WỌLÉ: No source was entered.")
                    return

                return self.execute_program(source, source_name="<paste>")

            self.paste_lines.append(line)
            return

        if self.declaration_lines is not None:
            keyword = line.strip().split(maxsplit=1)[0].upper() \
                if line.strip() else ""
            self.declaration_lines.append(line)

            if keyword in ("ISE", "BI", "NIGBATI", "FUN"):
                self.declaration_depth += 1
            elif keyword == "PARI":
                self.declaration_depth -= 1

                if self.declaration_depth == 0:
                    source = "\n".join(self.declaration_lines)
                    self.declaration_lines = None
                    self.prompt = "KỌ WỌLÉ > "
                    return self.execute_source(source)

            return

        if line.strip().upper().startswith("ISE "):
            self.declaration_lines = [line]
            self.declaration_depth = 1
            self.prompt = "......> "
            return

        return super().onecmd(line)

    def emptyline(self):

        if self.paste_lines is not None:
            self.paste_lines.append("")

        if self.declaration_lines is not None:
            self.declaration_lines.append("")

    def do_paste(self, arg):
        """
        Enter multi-line program mode. Finish with OTAN on its own line.
        """

        if arg.strip():
            print("Usage: PASTE")
            return

        self.paste_lines = []
        self.prompt = "......> "

    def do_otan(self, arg):
        """OTAN finishes a program entered using PASTE."""

        print("OTAN is used to finish PASTE mode. Enter PASTE first.")

    def do_end(self, arg):
        """END is retained as an alias for OTAN in PASTE mode."""

        print("END/OTAN finishes PASTE mode. Enter PASTE first.")

    def do_run(self, arg):
        """
        Parse and execute a complete OHÙN IFÁ source file.

        Usage:
            RUN <filename>
        """

        filename = arg.strip()

        if not filename:
            print("Usage: RUN <filename>")
            return

        requested = Path(filename).expanduser()
        candidates = [requested]

        if not requested.is_absolute():
            candidates.append(PROJECT_ROOT / requested)

        source_path = next(
            (path for path in candidates if path.is_file()),
            None,
        )

        if source_path is None:
            print(f"KÒ WỌLÉ: Source file not found: {filename}")
            return

        try:
            source = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            print(f"KÒ WỌLÉ: Unable to read {filename}: {error}")
            return

        return self.execute_program(
            source,
            source_name=str(source_path.resolve()),
        )

    def do_compile(self, arg):
        """Compile an OHÙN IFÁ file to build/<name>.ir and build/<name>.sv."""
        filename = arg.strip()
        if not filename:
            print("Usage: COMPILE <filename>"); return
        requested = Path(filename)
        source_path = requested if requested.is_file() else PROJECT_ROOT / requested
        if not source_path.is_file():
            print(f"KÒ WỌLÉ: Source file not found: {filename}"); return
        source = ""
        try:
            source = source_path.read_text(encoding="utf-8")
            ast = parser.parse_program(source, source_name=str(source_path.resolve()))
            ir = ir_lowerer.lower(ast_optimizer.optimize(ast))
            rtl = systemverilog_generator.generate(ir, source_path.stem)
            build_dir = PROJECT_ROOT / "build"
            build_dir.mkdir(parents=True, exist_ok=True)
            ir_path = build_dir / f"{source_path.stem}.ir"
            rtl_path = build_dir / f"{source_path.stem}.sv"
            ir_path.write_text(ir.to_text(), encoding="utf-8")
            rtl_path.write_text(rtl, encoding="utf-8")
        except Exception as error:
            print("KÒ WỌLÉ: " + format_diagnostic(
                error, source, str(source_path.resolve())
            ))
            return
        print(ir_path)
        print(rtl_path)

    # --------------------------------------------------
    # Backend
    # --------------------------------------------------

        # --------------------------------------------------
    # Backend
    # --------------------------------------------------

    def do_backend(self, arg):
        """
        Show or change the active backend.

        Usage:
            BACKEND
            BACKEND python
        """

        arg = arg.strip().lower()

        if not arg:
            print(f"Current backend: {backend_manager.backend_name}")
            print("Available:", ", ".join(backend_manager.available()))
            return

        try:
            backend_manager.use(arg)
            print(f"Backend changed to '{arg}'")
        except Exception as e:
            print(e)

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def do_status(self, arg):

        print()
        print("IFÁ Processor V4.5")
        print("------------------")
        print(f"Backend    : {backend_manager.backend_name}")
        print(f"YARA GBOBO : {'ON' if self.yara_gbobo else 'OFF'}")
        print()

    def do_services(self, arg):
        """Show native, non-security IFÁ V4.5 services."""
        print("IFÁ V4.5 NATIVE SERVICES")
        print("DAIFA / DÁIFÁ")
        print("PRINTODU / PRINTODUALL")
        print("OPELE / ÒPẸ̀LẸ̀ [LAST]")
        print("TEIFA <ODÙ> [ODÙ|MEJI] | <8 bits> | LAST")

    def do_suggestions(self, arg):
        """Show a short first-use command list."""
        print("SUGGESTIONS")
        print("HELP                 show all commands")
        print("SERVICES             show IFÁ services")
        print("2+2                  evaluate an expression")
        print("PAPO MEJI ATI META   run a native relation")
        print("RUN <file.ifa>       run an OHÙN program")
        print("IPO FRAME            inspect the last relation")
        print("EXIT                 leave the shell")


    # --------------------------------------------------
    # YARA
    # --------------------------------------------------

    def do_yara(self, arg):

        words = arg.strip().upper().split()

        if words == ["GBOBO"]:

            self.yara_gbobo = not self.yara_gbobo

            print(
                f"YARA GBOBO {'ENABLED' if self.yara_gbobo else 'DISABLED'}"
            )

            return

        print("Usage: YARA GBOBO")

    # --------------------------------------------------
    # IPO
    # --------------------------------------------------

    def do_ipo(self, arg):
        target = arg.strip().upper() or "FRAME"

        if target == "FRAME":
            channels = ifa_services_v45.last_channels
            frame = ifa_services_v45.last_frame
            if channels is None:
                print("IPO FRAME: no native execution recorded.")
                return
            print("IPO FRAME")
            if frame is not None:
                print(f"Relation : {frame.relation_id}")
                print(f"Operation: {frame.operation}")
                print(f"A/B      : {frame.operand_a} / {frame.operand_b}")
                print(f"VALUE    : {frame.VALUE}")
                print(f"VALID    : {int(frame.VALID)}")
            record = ifa_services_v45.last_backend_execution
            if frame is None and record is not None:
                print(f"Operation: {record.operation}")
                print(f"A/B      : {record.operand_a} / {record.operand_b}")
                print(f"VALUE    : {record.logical_result}")
            for name in ("y", "ra", "rd", "r0", "t"):
                print(f"{name.upper():<9}: 0x{channels[name]:02X}")
            return

        if target == "RMU":
            rmu = ifa_services_v45.rmu
            summary = rmu.summary()
            print("IPO RMU")
            for name in ("frames", "destinations", "fetches", "broadcasts"):
                print(f"{name.capitalize():<13}: {summary[name]}")
            for relation_id, frame in rmu.frames.items():
                print(f"{relation_id}: {frame.compact()}")
            return

        if target == "PHI":
            frame = ifa_services_v45.last_frame
            record = ifa_services_v45.last_backend_execution
            if frame is None and not all(
                hasattr(record, name) for name in ("phi_a", "phi_b", "phi_y")
            ):
                print("IPO PHI: no Φ-P8 execution recorded.")
                return
            print("IPO PHI")
            if record is not None and all(
                hasattr(record, name) for name in ("phi_a", "phi_b", "phi_y")
            ):
                values = (record.phi_a, record.phi_b, record.phi_y)
            else:
                values = tuple(
                    int("".join(str(bit) for bit in bits), 2)
                    for bits in (frame.PHI_A, frame.PHI_B, frame.PHI_Y)
                )
            for name, value in zip(("PHI_A", "PHI_B", "PHI_Y"), values):
                print(f"{name:<9}: 0x{value:02X} ({value:08b})")
            return

        print("Usage: IPO [FRAME|RMU|PHI]")

    # --------------------------------------------------
    # Default IFÁ command handler
    # --------------------------------------------------

    def default(self, line):

        #
        # ------------------------------------------
        # Make shell commands case-insensitive
        # ------------------------------------------
        #

        words = line.strip().split()

        if words:

            command = words[0].lower()
            args = " ".join(words[1:])

            if command == "help":
                return self.do_help(args)

            if command == "status":
                return self.do_status(args)

            if command == "services":
                return self.do_services(args)

            if command == "suggestions":
                return self.do_suggestions(args)

            if command == "backend":
                return self.do_backend(args)

            if command == "ipo":
                return self.do_ipo(args)

            if command == "yara":
                return self.do_yara(args)

            if command == "paste":
                return self.do_paste(args)

            if command == "otan":
                return self.do_otan(args)

            if command == "end":
                return self.do_end(args)

            if command == "run":
                return self.do_run(args)

            if command == "compile":
                return self.do_compile(args)

            if command in ("exit", "quit"):
                return self.do_exit(args)

        #
        # ------------------------------------------
        # IFÁ parser
        # ------------------------------------------
        #

        correction = correct_prime_sum(line)
        if correction is not None:
            print(render_correction(correction))
            return

        if ifa_services_v45.handle(line):
            return

        return self.execute_source(line)

    # --------------------------------------------------
    # Parse and execute IFÁ source
    # --------------------------------------------------

    def execute_source(self, source):

        try:
           ast = parser.parse(source, source_name="<interactive>")
           result = interpreter.execute(ast)

           if isinstance(ast, FunctionNode):
               result = ast

        except Exception as e:

            print("KÒ WỌLÉ: " + format_diagnostic(e, source, "<interactive>"))
            return

        if self.yara_gbobo:

            print()
            print("========== AST ==========")
            print(ast)
            print("-------------------------")
            print(result)
            print("================================")
            print()

        else:

            if result is not None:
                print(result)

    def execute_program(self, source, source_name="<program>"):

        try:
           ast = parser.parse_program(source, source_name=source_name)
           result = interpreter.execute(ast)

        except Exception as e:

            print("KÒ WỌLÉ: " + format_diagnostic(e, source, source_name))
            return

        if self.yara_gbobo:

            print()
            print("========== PROGRAM AST ==========")
            print(ast)
            print("---------------------------------")
            print(result)
            print("=================================")
            print()

        else:

            if result is not None:
                print(result)

    # --------------------------------------------------
    # Exit
    # --------------------------------------------------

    def do_exit(self, arg):

        print()
        print("Ó dàbọ̀  👋")
        print()

        return True

    do_quit = do_exit


def main(argv=None):
    argument_parser = argparse.ArgumentParser(
        description="OHÙN IFÁ Processor V4.5 interactive shell",
    )
    argument_parser.add_argument(
        "--backend", choices=("python", "rtl", "quantum"), default="python",
        help="initial execution backend (default: python)",
    )
    arguments = argument_parser.parse_args(argv)
    try:
        OhunIFAShell(backend_name=arguments.backend).cmdloop()
    except KeyboardInterrupt:
        print()
        print("Ó dàbọ̀ 👋")
        print()


if __name__ == "__main__":
    main()
