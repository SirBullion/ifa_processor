#!/usr/bin/env python3
"""Desktop launcher for the IFÁ v4.5 development and verification tools."""

from __future__ import annotations

import argparse
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


class IFALauncher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("IFÁ Processor v4.5")
        self.geometry("980x680")
        self.minsize(820, 560)
        self.output_queue: queue.Queue[str | None] = queue.Queue()
        self.running = False
        self.process: subprocess.Popen[str] | None = None
        self.interactive = False
        self.command_history: list[str] = []
        self.history_index = 0

        self.backend = tk.StringVar(value="python")
        self.hanoi_level = tk.IntVar(value=10)
        self.audit_program = tk.StringVar(
            value="programs_v4/hanoi_recursive_10_v45.ifa45"
        )
        self.status = tk.StringVar(value="Ready")

        self._build_ui()
        self.append(
            "FIRST TIME: click OHÙN shell or IFÁ monitor, then type HELP "
            "or SUGGESTIONS in KỌ WỌLÉ and press Enter.\n"
            "Correction example: SUM FIST 7 PTIME → Ó LÈ WỌLÉ — ÀTÚNṢE → 58.\n"
            "To audit hardware, select an .ifa45/.hex program and click "
            "Run + Audit + Wave.\n"
        )
        self.after(80, self._drain_output)
        self.protocol("WM_DELETE_WINDOW", self.close_launcher)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        title = ttk.Frame(self, padding=(16, 14, 16, 8))
        title.grid(row=0, column=0, sticky="ew")
        title.columnconfigure(0, weight=1)
        ttk.Label(title, text="IFÁ Processor v4.5", font=("TkDefaultFont", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(title, text="OHÙN · RTL · RMU · Quantum · Synthesis").grid(row=1, column=0, sticky="w")

        controls = ttk.LabelFrame(self, text="Launch and verify", padding=12)
        controls.grid(row=1, column=0, padx=16, pady=6, sticky="ew")
        for column in range(6):
            controls.columnconfigure(column, weight=1)

        ttk.Label(controls, text="Backend").grid(row=0, column=0, sticky="w")
        ttk.Combobox(controls, textvariable=self.backend, values=("python", "rtl", "quantum"), state="readonly", width=10).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(controls, text="OHÙN shell", command=self.open_shell).grid(row=1, column=1, sticky="ew", padx=4)
        ttk.Button(controls, text="IFÁ monitor", command=self.open_monitor).grid(row=1, column=2, sticky="ew", padx=4)
        ttk.Button(controls, text="Build RTL", command=lambda: self.run_command(["make", "v45-build"], "Building v4.5 RTL")).grid(row=1, column=3, sticky="ew", padx=4)
        ttk.Button(controls, text="Synthesize", command=lambda: self.run_command(["make", "v45-synth"], "Synthesizing v4.5 kernel")).grid(row=1, column=4, sticky="ew", padx=4)
        ttk.Button(controls, text="Run tests", command=self.run_tests).grid(row=1, column=5, sticky="ew", padx=(4, 0))

        ttk.Label(controls, text="Hanoi level").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Spinbox(controls, from_=5, to=10, textvariable=self.hanoi_level, width=8).grid(row=3, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(controls, text="Profile RMU", command=self.profile_hanoi).grid(row=3, column=1, sticky="ew", padx=4)
        ttk.Button(controls, text="GTKWave", command=self.open_wave).grid(row=3, column=2, sticky="ew", padx=4)
        ttk.Button(controls, text="Architecture", command=lambda: self.open_path(ROOT / "docs/IFA_PROCESSOR_ARCHITECTURE.md")).grid(row=3, column=3, sticky="ew", padx=4)
        ttk.Button(controls, text="Language docs", command=lambda: self.open_path(ROOT / "docs/OHUN_IFA_LANGUAGE_SPECIFICATION_1_0.md")).grid(row=3, column=4, sticky="ew", padx=4)
        ttk.Button(controls, text="EDA methods", command=lambda: self.open_path(ROOT / "docs/IFA_V45_EDA_OPEN_SOURCE_METHODS.md")).grid(row=3, column=5, sticky="ew", padx=(4, 0))

        ttk.Label(controls, text="Hardware program (.ifa45 or .hex)").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        ttk.Entry(controls, textvariable=self.audit_program).grid(
            row=5, column=0, columnspan=4, sticky="ew", padx=(0, 4)
        )
        ttk.Button(controls, text="Browse…", command=self.choose_audit_program).grid(
            row=5, column=4, sticky="ew", padx=4
        )
        ttk.Button(controls, text="Run + Audit + Wave", command=self.audit_selected_program).grid(
            row=5, column=5, sticky="ew", padx=(4, 0)
        )

        output_frame = ttk.LabelFrame(self, text="Integrated IFÁ console", padding=8)
        output_frame.grid(row=2, column=0, padx=16, pady=10, sticky="nsew")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        self.output = tk.Text(output_frame, wrap="word", font=("TkFixedFont", 10), state="disabled")
        scroll = ttk.Scrollbar(output_frame, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        command_bar = ttk.Frame(output_frame, padding=(0, 8, 0, 0))
        command_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        command_bar.columnconfigure(1, weight=1)
        ttk.Label(command_bar, text="KỌ WỌLÉ").grid(row=0, column=0, padx=(0, 8))
        self.command_entry = ttk.Entry(command_bar, font=("TkFixedFont", 10))
        self.command_entry.grid(row=0, column=1, sticky="ew")
        self.command_entry.bind("<Return>", self.send_console_command)
        self.command_entry.bind("<Up>", self.history_up)
        self.command_entry.bind("<Down>", self.history_down)
        ttk.Button(command_bar, text="Send", command=self.send_console_command).grid(row=0, column=2, padx=6)
        ttk.Button(command_bar, text="Stop", command=self.stop_process).grid(row=0, column=3)

        footer = ttk.Frame(self, padding=(16, 0, 16, 12))
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status).grid(row=0, column=0, sticky="w")
        ttk.Button(
            footer, text="First-time guide",
            command=lambda: self.open_path(ROOT / "docs/FIRST_TIME_IFA_V45.md"),
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(footer, text="Clear output", command=self.clear_output).grid(row=0, column=2)

    def append(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_output(self) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def run_command(self, command: list[str], label: str, stdin: str | None = None, interactive: bool = False) -> None:
        if self.running:
            messagebox.showinfo("IFÁ v4.5", "Another task is still running. Use Stop first.")
            return
        self.running = True
        self.interactive = interactive
        self.status.set(label)
        self.append(f"\n$ {' '.join(command)}\n")

        def worker() -> None:
            try:
                process = subprocess.Popen(
                    command, cwd=ROOT,
                    stdin=subprocess.PIPE if stdin is not None or interactive else None,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=0,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"},
                )
                self.process = process
                if stdin is not None and process.stdin is not None:
                    process.stdin.write(stdin)
                    process.stdin.close()
                assert process.stdout is not None
                while True:
                    character = process.stdout.read(1)
                    if character == "":
                        break
                    self.output_queue.put(character)
                code = process.wait()
                self.output_queue.put(f"\n[finished with status {code}]\n")
            except OSError as error:
                self.output_queue.put(f"KÒ WỌLÉ: {error}\n")
            finally:
                self.process = None
                self.output_queue.put(None)

        threading.Thread(target=worker, daemon=True).start()

    def _drain_output(self) -> None:
        try:
            while True:
                item = self.output_queue.get_nowait()
                if item is None:
                    self.running = False
                    self.interactive = False
                    self.status.set("Ready")
                else:
                    self.append(item)
        except queue.Empty:
            pass
        self.after(80, self._drain_output)

    def open_shell(self) -> None:
        self.run_command(
            [PYTHON, "-u", "tools/ohunifa_v45.py", "--backend", self.backend.get()],
            f"OHÙN shell ({self.backend.get()})", interactive=True,
        )
        self.command_entry.focus_set()

    def open_monitor(self) -> None:
        self.run_command(
            [PYTHON, "-u", "monitor_v45/ifa_monitor.py"],
            "IFÁ monitor", interactive=True,
        )
        self.command_entry.focus_set()

    def send_console_command(self, event=None):
        command = self.command_entry.get()
        if not self.interactive or self.process is None or self.process.stdin is None:
            messagebox.showinfo("IFÁ v4.5", "Start the OHÙN shell or IFÁ monitor first.")
            return "break"
        try:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            messagebox.showerror("IFÁ v4.5", str(error))
            return "break"
        self.append(command + "\n")
        if command.strip():
            self.command_history.append(command)
            self.history_index = len(self.command_history)
        self.command_entry.delete(0, "end")
        return "break"

    def history_up(self, event=None):
        if self.command_history:
            self.history_index = max(0, self.history_index - 1)
            self._set_command(self.command_history[self.history_index])
        return "break"

    def history_down(self, event=None):
        if self.command_history:
            self.history_index = min(len(self.command_history), self.history_index + 1)
            value = "" if self.history_index == len(self.command_history) else self.command_history[self.history_index]
            self._set_command(value)
        return "break"

    def _set_command(self, value: str) -> None:
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, value)
        self.command_entry.icursor("end")

    def stop_process(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()

    def close_launcher(self) -> None:
        self.stop_process()
        self.destroy()

    def run_tests(self) -> None:
        self.run_command([PYTHON, "-m", "unittest", "tests.test_v45_native_isa", "tests.test_quantum_backend"], "Running focused tests")

    def choose_audit_program(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self, title="Select an IFÁ v4.5 hardware program",
            initialdir=ROOT / "programs_v4",
            filetypes=(("IFÁ v4.5 assembly", "*.ifa45"), ("IFÁ instruction image", "*.hex"), ("All files", "*")),
        )
        if selected:
            try:
                self.audit_program.set(str(Path(selected).resolve().relative_to(ROOT)))
            except ValueError:
                self.audit_program.set(selected)

    def audit_selected_program(self) -> None:
        requested = Path(self.audit_program.get()).expanduser()
        program = requested if requested.is_absolute() else ROOT / requested
        if not program.is_file():
            messagebox.showerror("IFÁ v4.5", f"KÒ WỌLÉ: Program not found:\n{program}")
            return
        self.run_command(
            [PYTHON, "-u", "tools/ifa_v45_audit.py", str(program), "--open-wave"],
            f"Auditing {program.name}",
        )

    def profile_hanoi(self) -> None:
        level = self.hanoi_level.get()
        if level not in range(5, 11):
            messagebox.showerror("IFÁ v4.5", "Hanoi level must be from 5 through 10.")
            return
        image = ROOT / f"programs_v4/hanoi_recursive_{level}_v45.hex"
        if not image.is_file():
            messagebox.showerror("IFÁ v4.5", f"Missing program image: {image}")
            return
        commands = ["BABALAWO ON", "CREATE 0", "SELECT 0", "CONTEXT 00 0000 00 00 00 00 00"]
        commands.extend(f"LOAD {address:02x} {word.strip()}" for address, word in enumerate(image.read_text(encoding="utf-8").splitlines()))
        commands.extend(("RUN", "QUIT"))
        self.run_command(["vvp", "sim/v45/ifa_v45_os_bridge.out", "+INTERACTIVE"], f"Profiling Hanoi N={level}", "\n".join(commands) + "\n")

    def open_wave(self) -> None:
        wave = ROOT / f"sim/v45/hanoi_{self.hanoi_level.get()}_full_processor.fst"
        if not wave.is_file():
            messagebox.showerror("IFÁ v4.5", f"No waveform exists yet: {wave}")
            return
        try:
            subprocess.Popen(["gtkwave", str(wave)], cwd=ROOT)
        except OSError as error:
            messagebox.showerror("IFÁ v4.5", str(error))

    def open_path(self, path: Path) -> None:
        """Open project documentation without desktop file associations."""
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            messagebox.showerror("IFÁ v4.5", f"KÒ WỌLÉ: Unable to open {path}:\n{error}")
            return

        viewer = tk.Toplevel(self)
        viewer.title(f"IFÁ Documentation — {path.name}")
        viewer.geometry("900x700")
        viewer.minsize(640, 420)
        viewer.columnconfigure(0, weight=1)
        viewer.rowconfigure(0, weight=1)

        text = tk.Text(viewer, wrap="word", font=("TkFixedFont", 10))
        scroll = ttk.Scrollbar(viewer, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        text.insert("1.0", content)
        text.configure(state="disabled")


def check_environment() -> int:
    required = ("iverilog", "vvp", "gtkwave", "yosys", "verilator")
    missing = [name for name in required if shutil.which(name) is None]
    print(f"project_root={ROOT}")
    print("missing=" + (",".join(missing) if missing else "none"))
    return 1 if missing else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch the IFÁ v4.5 desktop interface")
    parser.add_argument("--check", action="store_true", help="check required open-source tools without opening the GUI")
    arguments = parser.parse_args()
    if arguments.check:
        return check_environment()
    IFALauncher().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
