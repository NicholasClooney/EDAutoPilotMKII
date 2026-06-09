from __future__ import annotations

from datetime import datetime
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import xml.etree.ElementTree as ET

import bindings_files
from edap.bindings_inventory import BindingsFileEntry


CUSTOM_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<Root PresetName="Custom" MajorVersion="4" MinorVersion="2">
\t<SetSpeedZero>
\t\t<Primary Device="Keyboard" Key="Key_X" />
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</SetSpeedZero>
</Root>
"""

BACKUP_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<Root PresetName="Custom" MajorVersion="4" MinorVersion="2">
\t<SetSpeedZero>
\t\t<Primary Device="Keyboard" Key="Key_Z" />
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</SetSpeedZero>
</Root>
"""

PRESET_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<Root PresetName="ControlPad" SortOrder="0">
\t<SetSpeedZero>
\t\t<Primary Device="Keyboard" Key="Key_C" />
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</SetSpeedZero>
</Root>
"""

KEYBOARD_MOUSE_BASE_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<Root PresetName="KeyboardMouseOnly" SortOrder="0">
\t<SetSpeedZero>
\t\t<Primary Device="Keyboard" Key="Key_C" />
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</SetSpeedZero>
\t<UI_Up>
\t\t<Primary Device="Keyboard" Key="Key_W" />
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</UI_Up>
</Root>
"""

CUSTOM_KEYBOARD_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<Root PresetName="Custom" MajorVersion="4" MinorVersion="2">
\t<SetSpeedZero>
\t\t<Primary Device="Keyboard" Key="Key_X" />
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</SetSpeedZero>
\t<UI_Up>
\t\t<Primary Device="Keyboard" Key="Key_W" />
\t\t<Secondary Device="Keyboard" Key="Key_UpArrow" />
\t</UI_Up>
</Root>
"""

CONTROL_PAD_BASE_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<Root PresetName="ControlPad" SortOrder="0">
\t<SetSpeedZero>
\t\t<Primary Device="GamePad" Key="Pad_A" />
\t\t<Secondary Device="Keyboard" Key="Key_C" />
\t</SetSpeedZero>
\t<UI_Up>
\t\t<Primary Device="GamePad" Key="Pad_DPadUp" />
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</UI_Up>
</Root>
"""

CONTROL_PAD_COMBO_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<Root PresetName="ControlPad" SortOrder="0">
\t<Supercruise>
\t\t<Primary Device="GamePad" Key="">
\t\t\t<Modifier Device="GamePad" Key="Pad_Back" />
\t\t</Primary>
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</Supercruise>
</Root>
"""

KEYBOARD_MOUSE_SUPERCRUISE_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<Root PresetName="KeyboardMouseOnly" SortOrder="0">
\t<Supercruise>
\t\t<Primary Device="{NoDevice}" Key="" />
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</Supercruise>
</Root>
"""

CUSTOM_SUPERCRUISE_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<Root PresetName="Custom" MajorVersion="4" MinorVersion="2">
\t<Supercruise>
\t\t<Primary Device="Keyboard" Key="Key_J" />
\t\t<Secondary Device="{NoDevice}" Key="" />
\t</Supercruise>
</Root>
"""


class BindingsFilesCliTests(unittest.TestCase):
    def test_filter_entries_matches_prefix_against_name_and_preset(self) -> None:
        entries = [
            BindingsFileEntry(path=Path("/tmp/Alpha.binds"), modified_at=datetime(2026, 6, 9, 10, 0, 0)),
            BindingsFileEntry(path=Path("/tmp/Beta.binds"), modified_at=datetime(2026, 6, 9, 10, 0, 1)),
        ]

        filtered = bindings_files._filter_entries(entries, "be")

        self.assertEqual([entry.name for entry in filtered], ["Beta.binds"])

    def test_backup_command_copies_selected_bindings_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bindings_dir = root / "bindings"
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            detected.parent.mkdir(parents=True)
            detected.write_text(CUSTOM_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "sys.stdout", new_callable=io.StringIO
            ) as stdout, patch("sys.stderr", new_callable=io.StringIO):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "backup",
                        "latest",
                        "--backup-dir",
                        str(backup_dir),
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            copies = sorted(backup_dir.glob("*.binds"))
            self.assertEqual(len(copies), 1)
            self.assertEqual(copies[0].read_text(encoding="utf-8"), CUSTOM_XML)
            self.assertIn("Copied Custom.4.2.binds", stdout.getvalue())

    def test_restore_command_uses_numeric_selector_and_backs_up_current_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bindings_dir = root / "bindings"
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            detected.parent.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_XML, encoding="utf-8")
            restored = backup_dir / "Custom.4.2-2026-06-09.binds"
            restored.write_text(BACKUP_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "sys.stdout", new_callable=io.StringIO
            ) as stdout, patch("sys.stderr", new_callable=io.StringIO):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "restore",
                        "1",
                        "--backup-dir",
                        str(backup_dir),
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(detected.read_text(encoding="utf-8"), BACKUP_XML)
            backups = sorted(path for path in backup_dir.glob("*.binds") if path != restored)
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), CUSTOM_XML)
            self.assertIn("Backed up current bindings to", stdout.getvalue())
            self.assertIn("Restored", stdout.getvalue())

    def test_restore_command_interactive_selection_uses_helper(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bindings_dir = root / "bindings"
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            detected.parent.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_XML, encoding="utf-8")
            first = backup_dir / "A.binds"
            second = backup_dir / "B.binds"
            first.write_text(CUSTOM_XML, encoding="utf-8")
            second.write_text(BACKUP_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "bindings_files._choose_entry_interactively",
                side_effect=lambda entries, *_args, **_kwargs: next(
                    entry for entry in entries if entry.name == "B.binds"
                ),
            ), patch("sys.stdout", new_callable=io.StringIO), patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "restore",
                        "--backup-dir",
                        str(backup_dir),
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(detected.read_text(encoding="utf-8"), BACKUP_XML)

    def test_interactive_selector_supports_prefix_filter(self) -> None:
        entries = [
            BindingsFileEntry(path=Path("/tmp/Alpha.binds"), modified_at=datetime(2026, 6, 9, 10, 0, 0)),
            BindingsFileEntry(path=Path("/tmp/Beta.binds"), modified_at=datetime(2026, 6, 9, 10, 0, 1)),
        ]

        class _FakeTTY(io.StringIO):
            def isatty(self) -> bool:
                return True

            def fileno(self) -> int:
                return 0

        fake_stdin = _FakeTTY()
        fake_stdout = _FakeTTY()

        with patch("sys.stdin", fake_stdin), patch("sys.stdout", fake_stdout), patch(
            "bindings_files.os.name", "posix"
        ), patch("bindings_files.termios", object()), patch("bindings_files.tty", object()), patch(
            "bindings_files._read_key",
            side_effect=["b", "\n"],
        ):
            selected = bindings_files._choose_entry_interactively(entries, label="backup file")

        self.assertEqual(selected.name, "Beta.binds")

    def test_interactive_selector_ctrl_c_cancels(self) -> None:
        entries = [
            BindingsFileEntry(path=Path("/tmp/Alpha.binds"), modified_at=datetime(2026, 6, 9, 10, 0, 0)),
        ]

        class _FakeTTY(io.StringIO):
            def isatty(self) -> bool:
                return True

            def fileno(self) -> int:
                return 0

        fake_stdin = _FakeTTY()
        fake_stdout = _FakeTTY()

        with patch("sys.stdin", fake_stdin), patch("sys.stdout", fake_stdout), patch(
            "bindings_files.os.name", "posix"
        ), patch("bindings_files.termios", object()), patch("bindings_files.tty", object()), patch(
            "bindings_files._read_key",
            side_effect=["\x03"],
        ):
            with self.assertRaisesRegex(ValueError, "selection cancelled"):
                bindings_files._choose_entry_interactively(entries, label="backup file")

    def test_apply_default_command_confirms_and_preserves_custom_root_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bottle = root / "BottleA/drive_c"
            bindings_dir = (
                bottle
                / "users/crossover/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings"
            )
            preset_dir = (
                bottle
                / "Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/ControlSchemes"
            )
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            preset = preset_dir / "ControlPad.binds"
            detected.parent.mkdir(parents=True)
            preset.parent.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_XML, encoding="utf-8")
            preset.write_text(PRESET_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "bindings_files._confirm_overwrite",
                return_value=True,
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout, patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "apply-default",
                        "1",
                        "--backup-dir",
                        str(backup_dir),
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            root_el = ET.parse(detected).getroot()
            self.assertEqual(root_el.attrib["PresetName"], "Custom")
            self.assertEqual(root_el.attrib["MajorVersion"], "4")
            self.assertEqual(root_el.attrib["MinorVersion"], "2")
            self.assertEqual(root_el.find("SetSpeedZero/Primary").attrib["Key"], "Key_C")
            backups = sorted(backup_dir.glob("*.binds"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), CUSTOM_XML)
            self.assertIn("Backed up current bindings to", stdout.getvalue())
            self.assertIn("Applied preset ControlPad", stdout.getvalue())

    def test_apply_default_command_can_emit_json(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bottle = root / "BottleA/drive_c"
            bindings_dir = (
                bottle
                / "users/crossover/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings"
            )
            preset_dir = (
                bottle
                / "Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/ControlSchemes"
            )
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            preset = preset_dir / "ControlPad.binds"
            detected.parent.mkdir(parents=True)
            preset.parent.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_XML, encoding="utf-8")
            preset.write_text(PRESET_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "bindings_files._confirm_overwrite",
                return_value=True,
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout, patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "--json",
                        "apply-default",
                        "1",
                        "--backup-dir",
                        str(backup_dir),
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["preset_name"], "ControlPad")
            self.assertEqual(payload["target"], str(detected))
            self.assertTrue(payload["backup"].endswith(".binds"))

    def test_apply_default_command_stops_when_not_confirmed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bottle = root / "BottleA/drive_c"
            bindings_dir = (
                bottle
                / "users/crossover/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings"
            )
            preset_dir = (
                bottle
                / "Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/ControlSchemes"
            )
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            preset = preset_dir / "ControlPad.binds"
            detected.parent.mkdir(parents=True)
            preset.parent.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_XML, encoding="utf-8")
            preset.write_text(PRESET_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "bindings_files._confirm_overwrite",
                return_value=False,
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout, patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "apply-default",
                        "1",
                        "--backup-dir",
                        str(backup_dir),
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(detected.read_text(encoding="utf-8"), CUSTOM_XML)
            self.assertEqual(list(backup_dir.glob("*.binds")), [])
            self.assertIn("Cancelled.", stdout.getvalue())

    def test_port_default_command_ports_keyboard_deltas_onto_target_preset(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bottle = root / "BottleA/drive_c"
            bindings_dir = (
                bottle
                / "users/crossover/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings"
            )
            preset_dir = (
                bottle
                / "Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/ControlSchemes"
            )
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            keyboard_mouse = preset_dir / "KeyboardMouseOnly.binds"
            control_pad = preset_dir / "ControlPad.binds"
            detected.parent.mkdir(parents=True)
            preset_dir.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_KEYBOARD_XML, encoding="utf-8")
            keyboard_mouse.write_text(KEYBOARD_MOUSE_BASE_XML, encoding="utf-8")
            control_pad.write_text(CONTROL_PAD_BASE_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "bindings_files._confirm_overwrite",
                return_value=True,
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout, patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "port-default",
                        "KeyboardMouseOnly",
                        "ControlPad",
                        "--backup-dir",
                        str(backup_dir),
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            root_el = ET.parse(detected).getroot()
            self.assertEqual(root_el.attrib["PresetName"], "Custom")
            self.assertEqual(root_el.attrib["MajorVersion"], "4")
            self.assertEqual(root_el.attrib["MinorVersion"], "2")
            self.assertEqual(root_el.find("SetSpeedZero/Primary").attrib["Device"], "GamePad")
            self.assertEqual(root_el.find("SetSpeedZero/Secondary").attrib["Key"], "Key_X")
            self.assertEqual(root_el.find("UI_Up/Primary").attrib["Device"], "GamePad")
            self.assertEqual(root_el.find("UI_Up/Secondary").attrib["Key"], "Key_UpArrow")
            backups = sorted(backup_dir.glob("*.binds"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), CUSTOM_KEYBOARD_XML)
            self.assertIn("Preview: port keyboard changes from KeyboardMouseOnly onto ControlPad", stdout.getvalue())
            self.assertIn(
                "Set Speed to 0% (Ship Controls > Flight Throttle) [SetSpeedZero] | Secondary slot from Keyboard C to Keyboard X | based on Primary change",
                stdout.getvalue(),
            )
            self.assertIn(
                "UI Panel Up (General Controls > Interface Mode) [UI_Up] | Secondary slot from Unbound to Keyboard Up Arrow | based on Secondary change",
                stdout.getvalue(),
            )
            self.assertIn("Ported 2 keyboard change(s)", stdout.getvalue())

    def test_port_default_command_can_emit_json(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bottle = root / "BottleA/drive_c"
            bindings_dir = (
                bottle
                / "users/crossover/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings"
            )
            preset_dir = (
                bottle
                / "Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/ControlSchemes"
            )
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            keyboard_mouse = preset_dir / "KeyboardMouseOnly.binds"
            control_pad = preset_dir / "ControlPad.binds"
            detected.parent.mkdir(parents=True)
            preset_dir.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_KEYBOARD_XML, encoding="utf-8")
            keyboard_mouse.write_text(KEYBOARD_MOUSE_BASE_XML, encoding="utf-8")
            control_pad.write_text(CONTROL_PAD_BASE_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "bindings_files._confirm_overwrite",
                return_value=True,
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout, patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "--json",
                        "port-default",
                        "KeyboardMouseOnly",
                        "ControlPad",
                        "--backup-dir",
                        str(backup_dir),
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["source_base"]["preset_name"], "KeyboardMouseOnly")
            self.assertEqual(payload["target_base"]["preset_name"], "ControlPad")
            self.assertEqual(payload["applied_count"], 2)
            self.assertEqual(payload["target"], str(detected))
            self.assertEqual(
                payload["applied"][0]["from"],
                {"device": "Keyboard", "key": "Key_C", "modifier": None},
            )

    def test_port_default_command_dry_run_previews_without_writing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bottle = root / "BottleA/drive_c"
            bindings_dir = (
                bottle
                / "users/crossover/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings"
            )
            preset_dir = (
                bottle
                / "Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/ControlSchemes"
            )
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            keyboard_mouse = preset_dir / "KeyboardMouseOnly.binds"
            control_pad = preset_dir / "ControlPad.binds"
            detected.parent.mkdir(parents=True)
            preset_dir.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_KEYBOARD_XML, encoding="utf-8")
            keyboard_mouse.write_text(KEYBOARD_MOUSE_BASE_XML, encoding="utf-8")
            control_pad.write_text(CONTROL_PAD_BASE_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "bindings_files._confirm_overwrite",
                side_effect=AssertionError("dry run should not prompt"),
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout, patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "port-default",
                        "KeyboardMouseOnly",
                        "ControlPad",
                        "--backup-dir",
                        str(backup_dir),
                        "--dry-run",
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(detected.read_text(encoding="utf-8"), CUSTOM_KEYBOARD_XML)
            self.assertEqual(list(backup_dir.glob("*.binds")), [])
            self.assertIn("Preview: port keyboard changes from KeyboardMouseOnly onto ControlPad", stdout.getvalue())
            self.assertIn("Dry run only. No changes written.", stdout.getvalue())
            self.assertNotIn("Unbound to Unbound", stdout.getvalue())

    def test_port_default_command_dry_run_json_previews_without_writing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bottle = root / "BottleA/drive_c"
            bindings_dir = (
                bottle
                / "users/crossover/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings"
            )
            preset_dir = (
                bottle
                / "Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/ControlSchemes"
            )
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            keyboard_mouse = preset_dir / "KeyboardMouseOnly.binds"
            control_pad = preset_dir / "ControlPad.binds"
            detected.parent.mkdir(parents=True)
            preset_dir.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_KEYBOARD_XML, encoding="utf-8")
            keyboard_mouse.write_text(KEYBOARD_MOUSE_BASE_XML, encoding="utf-8")
            control_pad.write_text(CONTROL_PAD_BASE_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "bindings_files._confirm_overwrite",
                side_effect=AssertionError("dry run should not prompt"),
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout, patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "--json",
                        "port-default",
                        "KeyboardMouseOnly",
                        "ControlPad",
                        "--backup-dir",
                        str(backup_dir),
                        "--dry-run",
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["applied_count"], 2)
            self.assertNotIn("backup", payload)
            self.assertEqual(detected.read_text(encoding="utf-8"), CUSTOM_KEYBOARD_XML)

    def test_port_default_command_treats_gamepad_combo_slot_as_occupied(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bottle = root / "BottleA/drive_c"
            bindings_dir = (
                bottle
                / "users/crossover/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings"
            )
            preset_dir = (
                bottle
                / "Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/ControlSchemes"
            )
            backup_dir = root / "backup"
            detected = bindings_dir / "Custom.4.2.binds"
            keyboard_mouse = preset_dir / "KeyboardMouseOnly.binds"
            control_pad = preset_dir / "ControlPad.binds"
            detected.parent.mkdir(parents=True)
            preset_dir.mkdir(parents=True)
            backup_dir.mkdir(parents=True)
            detected.write_text(CUSTOM_SUPERCRUISE_XML, encoding="utf-8")
            keyboard_mouse.write_text(KEYBOARD_MOUSE_SUPERCRUISE_XML, encoding="utf-8")
            control_pad.write_text(CONTROL_PAD_COMBO_XML, encoding="utf-8")

            with patch("bindings_files._resolve_bindings_file", return_value=detected), patch(
                "bindings_files._confirm_overwrite",
                side_effect=AssertionError("dry run should not prompt"),
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout, patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                with patch(
                    "sys.argv",
                    [
                        "bindings_files.py",
                        "--bindings-file",
                        str(detected),
                        "port-default",
                        "KeyboardMouseOnly",
                        "ControlPad",
                        "--backup-dir",
                        str(backup_dir),
                        "--dry-run",
                    ],
                ):
                    exit_code = bindings_files.main()

            self.assertEqual(exit_code, 0)
            self.assertIn(
                "Supercruise [Supercruise] | Secondary slot from Unbound to Keyboard J | based on Primary change",
                stdout.getvalue(),
            )
            self.assertNotIn(
                "Supercruise [Supercruise] | Primary slot from Unbound to Keyboard J | based on Primary change",
                stdout.getvalue(),
            )
