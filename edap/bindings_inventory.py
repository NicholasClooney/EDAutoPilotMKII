from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element


DEFAULT_BACKUP_DIR = Path("backup/bindings")


@dataclass(frozen=True)
class BindingsFileEntry:
    path: Path
    modified_at: datetime

    @property
    def name(self) -> str:
        return self.path.name


@dataclass(frozen=True)
class PresetFileEntry:
    path: Path
    modified_at: datetime
    preset_name: str

    @property
    def name(self) -> str:
        return self.path.name


def list_bindings_files(bindings_dir: Path) -> list[BindingsFileEntry]:
    entries = [
        BindingsFileEntry(
            path=path,
            modified_at=datetime.fromtimestamp(path.stat().st_mtime),
        )
        for path in bindings_dir.glob("*.binds")
        if path.is_file()
    ]
    return sorted(entries, key=lambda entry: (-entry.modified_at.timestamp(), entry.name.lower()))


def choose_bindings_file(entries: list[BindingsFileEntry], selector: str | None = None) -> BindingsFileEntry:
    if not entries:
        raise ValueError("no .binds files found in detected bindings folder")
    if selector is None or selector == "latest":
        return entries[0]
    if selector.isdigit():
        index = int(selector)
        if 1 <= index <= len(entries):
            return entries[index - 1]

    for entry in entries:
        if entry.name == selector or str(entry.path) == selector:
            return entry

    raise ValueError(f"could not find .binds file matching {selector!r}")


def default_backup_name(bindings_path: Path, *, today: date | None = None) -> str:
    stamp = (today or date.today()).strftime("%Y-%m-%d")
    return f"{bindings_path.stem}-{stamp}{bindings_path.suffix}"


def copy_bindings_to_backup(
    source: Path,
    *,
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    backup_name: str | None = None,
) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)

    target_name = backup_name or default_backup_name(source)
    target = backup_dir / target_name
    if target.suffix != source.suffix:
        target = target.with_suffix(source.suffix)

    if target.exists():
        base = target.stem
        suffix = target.suffix
        counter = 2
        while True:
            candidate = backup_dir / f"{base}-{counter}{suffix}"
            if not candidate.exists():
                target = candidate
                break
            counter += 1

    shutil.copy2(source, target)
    return target


def list_backup_files(backup_dir: Path = DEFAULT_BACKUP_DIR) -> list[BindingsFileEntry]:
    if not backup_dir.exists():
        return []
    return list_bindings_files(backup_dir)


def list_default_preset_files(bindings_file: Path) -> list[PresetFileEntry]:
    entries: list[PresetFileEntry] = []
    seen_paths: set[Path] = set()
    for control_schemes_dir in _control_schemes_dirs(bindings_file):
        for path in sorted(control_schemes_dir.glob("*.binds"), key=lambda item: item.name.lower()):
            if not path.is_file() or path in seen_paths:
                continue
            seen_paths.add(path)
            entries.append(
                PresetFileEntry(
                    path=path,
                    modified_at=datetime.fromtimestamp(path.stat().st_mtime),
                    preset_name=_read_preset_name(path),
                )
            )
    return sorted(entries, key=lambda entry: (entry.preset_name.lower(), entry.name.lower()))


def restore_bindings_file(source: Path, target: Path) -> None:
    shutil.copy2(source, target)


def apply_preset_to_bindings_file(source: Path, target: Path) -> None:
    source_tree = ET.parse(source)
    _preserve_target_root_metadata(source_tree, target)

    ET.indent(source_tree, space="\t", level=0)
    source_tree.write(target, encoding="utf-8", xml_declaration=True, short_empty_elements=True)


def port_keyboard_changes_to_preset(
    source_custom: Path,
    *,
    source_preset: Path,
    target_preset: Path,
    target_file: Path,
    dry_run: bool = False,
) -> dict[str, object]:
    source_custom_tree = ET.parse(source_custom)
    source_preset_tree = ET.parse(source_preset)
    target_tree = ET.parse(target_preset)
    _preserve_target_root_metadata(target_tree, target_file)

    source_custom_root = source_custom_tree.getroot()
    source_preset_root = source_preset_tree.getroot()
    target_root = target_tree.getroot()

    applied: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []

    for action_name in _action_names(source_custom_root, source_preset_root):
        source_custom_action = source_custom_root.find(action_name)
        source_preset_action = source_preset_root.find(action_name)
        for source_slot_name in ("Primary", "Secondary"):
            custom_slot = _slot_for(source_custom_action, source_slot_name)
            preset_slot = _slot_for(source_preset_action, source_slot_name)
            if _slot_signature(custom_slot) == _slot_signature(preset_slot):
                continue
            if not _is_keyboard_delta(custom_slot, preset_slot):
                continue

            target_action = target_root.find(action_name)
            if target_action is None:
                target_action = ET.SubElement(target_root, action_name)

            target_slot_name = _choose_target_slot_name(
                target_action=target_action,
                preferred_slot_name=source_slot_name,
            )
            if target_slot_name is None:
                skipped.append({"action": action_name, "source_slot": source_slot_name})
                continue

            before_payload = _slot_payload(_slot_for(target_action, target_slot_name))
            after_payload = _slot_payload(custom_slot)
            if before_payload == after_payload:
                continue
            _apply_slot_copy(target_action, target_slot_name, custom_slot)
            applied.append(
                {
                    "action": action_name,
                    "source_slot": source_slot_name,
                    "target_slot": target_slot_name,
                    "from": before_payload,
                    "to": after_payload,
                }
            )

    result = {
        "applied": applied,
        "applied_count": len(applied),
        "skipped": skipped,
        "skipped_count": len(skipped),
    }
    if dry_run:
        return result

    ET.indent(target_tree, space="\t", level=0)
    target_tree.write(target_file, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    return result


def _control_schemes_dirs(bindings_file: Path) -> list[Path]:
    candidates: list[Path] = []
    roots: list[Path] = []

    for parent in bindings_file.parents:
        if parent.name == "drive_c":
            roots.append(parent)
            break

    anchor = Path(bindings_file.anchor) if bindings_file.anchor and bindings_file.anchor not in {"/", "\\"} else None
    if anchor is not None and anchor.exists():
        roots.append(anchor)

    seen: set[Path] = set()
    ordered_roots: list[Path] = []
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        ordered_roots.append(root)

    patterns = [
        "Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/*/ControlSchemes",
        "Program Files/Steam/steamapps/common/Elite Dangerous/Products/*/ControlSchemes",
        "**/Elite Dangerous/Products/*/ControlSchemes",
    ]
    for root in ordered_roots:
        for pattern in patterns:
            for path in root.glob(pattern):
                if path.is_dir():
                    candidates.append(path)

    unique = sorted(set(candidates), key=lambda path: str(path))
    return unique


def _read_preset_name(path: Path) -> str:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return path.stem
    return root.attrib.get("PresetName", path.stem)


def _preserve_target_root_metadata(source_tree: ET.ElementTree, target: Path) -> None:
    source_root = source_tree.getroot()
    if not target.exists():
        return
    target_root = ET.parse(target).getroot()
    for key in ("PresetName", "MajorVersion", "MinorVersion"):
        if key in target_root.attrib:
            source_root.attrib[key] = target_root.attrib[key]


def _action_names(*roots: Element) -> list[str]:
    names: set[str] = set()
    for root in roots:
        for child in root:
            names.add(child.tag)
    return sorted(names)


def _slot_for(action: Element | None, slot_name: str) -> Element | None:
    if action is None:
        return None
    return action.find(slot_name)


def _slot_signature(slot: Element | None) -> tuple[str, str, str | None] | None:
    if slot is None:
        return None
    modifier = slot.find("Modifier")
    return (
        slot.attrib.get("Device", "").strip(),
        slot.attrib.get("Key", "").strip(),
        modifier.attrib.get("Key", "").strip() if modifier is not None else None,
    )


def _slot_payload(slot: Element | None) -> dict[str, str | None]:
    signature = _slot_signature(slot)
    if signature is None:
        return {"device": "", "key": "", "modifier": None}
    device, key, modifier = signature
    return {"device": device, "key": key, "modifier": modifier}


def _is_keyboard_delta(custom_slot: Element | None, preset_slot: Element | None) -> bool:
    return _is_keyboard_like(custom_slot) or _is_keyboard_like(preset_slot) or (
        _is_unbound(custom_slot) and _is_keyboard_like(preset_slot)
    )


def _is_keyboard_like(slot: Element | None) -> bool:
    return _device_name(slot) == "Keyboard"


def _is_unbound(slot: Element | None) -> bool:
    if slot is None:
        return True
    device = _device_name(slot)
    key = slot.attrib.get("Key", "").strip()
    has_modifier = slot.find("Modifier") is not None
    return (device in {"", "{NoDevice}"}) or (not key and not has_modifier)


def _device_name(slot: Element | None) -> str:
    if slot is None:
        return ""
    return slot.attrib.get("Device", "").strip()


def _choose_target_slot_name(*, target_action: Element, preferred_slot_name: str) -> str | None:
    candidates = [preferred_slot_name, "Secondary" if preferred_slot_name == "Primary" else "Primary"]
    for slot_name in candidates:
        slot = target_action.find(slot_name)
        if _is_keyboard_like(slot) or _is_unbound(slot):
            return slot_name
    if preferred_slot_name == "Primary":
        return "Secondary"
    return preferred_slot_name


def _apply_slot_copy(target_action: Element, slot_name: str, source_slot: Element | None) -> None:
    target_slot = target_action.find(slot_name)
    if target_slot is None:
        target_slot = ET.SubElement(target_action, slot_name)

    target_slot.attrib.clear()
    for child in list(target_slot):
        target_slot.remove(child)

    if source_slot is None:
        target_slot.set("Device", "{NoDevice}")
        target_slot.set("Key", "")
        return

    for key, value in source_slot.attrib.items():
        target_slot.set(key, value)
    for child in list(source_slot):
        target_slot.append(ET.fromstring(ET.tostring(child, encoding="unicode")))
