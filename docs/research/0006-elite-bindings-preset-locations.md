# 0006: Elite Bindings Preset Locations Under CrossOver

Date: 2026-06-09

## Scope

This note records where Elite Dangerous gets the control-presets dropdown entries under the current macOS + CrossOver + Steam setup, which parts are user-editable versus shipped with the game, and how controller bindings are represented in the XML.

Question answered:

- Why does the in-game presets dropdown show many default mappings when the user's `Options/Bindings` folder only contains one custom `.binds` file?
- How does Elite record controller inputs inside `.binds` files?

## Short Answer

The presets dropdown is composed from two different sources:

- shipped preset `.binds` files in the game install's `ControlSchemes` folder
- user-created `.binds` files in the per-user `Options/Bindings` folder

The writable `Options/Bindings` folder is not expected to contain the built-in presets.

## Verified CrossOver Paths

Built-in presets:

- `/Users/nicholasclooney/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/ControlSchemes`

User bindings:

- `/Users/nicholasclooney/Library/Application Support/CrossOver/Bottles/Steam/drive_c/users/crossover/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings`

## Verified Built-In Preset Files

Observed shipped `.binds` files included:

- `AdvancedControlPad.binds`
- `AdvancedControlPad2.binds`
- `ClassicKeyboardOnly.binds`
- `ControlPad.binds`
- `ControlPadYaw.binds`
- `DualShock4Controller.binds`
- `DualShock4ControllerYaw.binds`
- `Empty.binds`
- `KeyboardMouseOnly.binds`
- `KeyboardMouseOnlyYaw.binds`

Additional HOTAS/joystick presets are also present in the same folder.

## Verified User Bindings Folder Contents

Observed contents of the writable bindings folder:

- `Custom.4.2.binds`
- `StartPreset.4.start`
- `BindingLoadingErrors.log`
- several local backup copies of `Custom.4.2.binds`

This confirms the user's observation: only the custom binding lives in the writable Frontier folder, while the default presets live in the install tree.

## Current Preset Selection Marker

`StartPreset.4.start` currently contains:

```text
Custom
Custom
Custom
KeyboardMouseOnly
```

Interpretation:

- `Custom.4.2.binds` is the active user preset on the relevant sections
- `KeyboardMouseOnly` remains present as a built-in preset reference/fallback entry

## Dropdown Label Mapping

The internal preset file names do not exactly match the human-facing labels shown in the Odyssey controls UI.

Confirmed likely mappings from the observed screenshots and shipped filenames:

- `CONTROL PAD ALTERNATE 2` -> `AdvancedControlPad.binds`
- `CONTROL PAD ALTERNATE 3` -> `AdvancedControlPad2.binds`
- `CONTROL PAD DEFAULT` -> `ControlPad.binds`
- `KEYBOARD WITHOUT MOUSE` -> `ClassicKeyboardOnly.binds`
- `CONTROL PAD WITH KEYBOARD & MOUSE` / yaw variant -> `KeyboardMouseOnly*.binds`
- `DUALSHOCK®4` / `DUALSHOCK®4 YAW` -> `DualShock4Controller*.binds`
- `BLANK` -> `Empty.binds`

This mapping is inferred from the file inventory plus the in-game labels, not from a Frontier-authored label table.

## Controller Binding Representation

Elite stores controller bindings in `.binds` as symbolic device-and-control tokens, not as raw sampled axis values.

Observed shape:

- `Device="..."` stores the logical device name
- `Key="..."` stores the button/axis token on that device

Examples from shipped presets:

- Xbox/gamepad axes and buttons:
  - `Device="XB360 Pad" Key="Pad_LStickX"`
  - `Device="XB360 Pad" Key="Pad_LStickY"`
  - `Device="XB360 Pad" Key="Pad_RBumper"`
- HOTAS/joystick axes and buttons:
  - `Device="SaitekX56Joystick" Key="Joy_XAxis"`
  - `Device="SaitekX56Joystick" Key="Joy_RZAxis"`
  - `Device="SaitekX56Joystick" Key="Joy_1"`
- Keyboard/mouse entries use the same model:
  - `Device="Keyboard" Key="Key_Space"`
  - `Device="Mouse" Key="Mouse_1"`

Axis bindings also carry tuning fields in the same XML node:

- `<Inverted Value="0|1" />`
- `<Deadzone Value="..." />`

So the binding file records "which named control on which named device", plus axis settings, rather than persisting live numeric axis positions.

## Device Identification Layer

The logical `Device="..."` names in `.binds` are backed by a separate install-time mapping file:

- `.../ControlSchemes/DeviceMappings.xml`

That file maps device families and named devices to USB identity information such as `VID` and `PID`.

Examples observed:

- `GamePad` contains many Xbox-compatible `VID`/`PID` alternatives
- `SaitekX56Joystick` maps to `PID 2221`, `VID 0738`
- `DualShock4` maps to `VID 054C` plus several `PID` alternatives

Practical interpretation:

1. `.binds` stores the logical device name plus control token
2. `DeviceMappings.xml` tells Elite which real hardware matches that logical name
3. per-axis inversion/deadzone remain on the binding node itself

## Common Token Families

Observed token families include:

- gamepad: `Pad_LStickX`, `Pad_RStickY`, `Pad_RBumper`
- joystick/HOTAS: `Joy_XAxis`, `Joy_YAxis`, `Joy_RZAxis`, `Joy_1`
- keyboard: `Key_W`, `Key_Space`
- mouse: `Mouse_1`

## Practical Implications For EDAP

- A tool that only scans `Options/Bindings/*.binds` will only see user-created profiles, not Frontier defaults.
- If EDAP ever needs to inventory all selectable presets, it must optionally read both the writable `Options/Bindings` folder and the installed `ControlSchemes` folder.
- Any future controller/HOTAS introspection feature should treat `.binds` as symbolic mappings and use `DeviceMappings.xml` when it needs hardware identity context.
- For operator backup/restore flows, the writable `Options/Bindings` folder remains the correct target because that is where edited custom profiles and `StartPreset*.start` live.

## Follow-Up Options

If future operator tooling needs it, a small helper could:

1. list shipped presets from `ControlSchemes`
2. list user presets from `Options/Bindings`
3. show which preset names are currently referenced by `StartPreset*.start`
