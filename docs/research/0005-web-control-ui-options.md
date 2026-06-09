# 0005: Web Control UI Options

Date: 2026-06-09

## Scope

This note records the initial tradeoff discussion around a phone-accessible Control Room UI so the repo can resume that work later without re-litigating the same first-pass questions.

Current desired scope:

- fastest possible prototype
- mostly one operator
- LAN-only access
- limited polish
- stay mostly in Python

This is explicitly not a multi-user/auth/product-surface design exercise yet.

## Options Considered

Rough menu of "easiest way to add a web UI to a Python repo," ordered by how little new tooling each one introduces:

1. **FastAPI + WebSockets + a static HTML/JS page.** First-class WebSocket support, can serve static files, client can be a single `index.html` with vanilla JS or htmx plus a small WS snippet. No JS build step, no node toolchain. Most flexible long-term ceiling.
2. **Flask + Flask-SocketIO.** Mature and well-documented. Slightly heavier (Socket.IO protocol, needs a JS client lib). Good built-in rooms/broadcast semantics.
3. **Starlette directly.** What FastAPI is built on. Lighter if we do not need REST/OpenAPI ergonomics. Usually not worth the savings.
4. **Pure-Python UI frameworks (NiceGUI, Reflex, Streamlit).** No hand-written JS. NiceGUI in particular is well-suited to control panels and has WebSocket-backed reactivity built in. Tradeoff: locked into the framework's component model, and mobile polish varies by framework.

NiceGUI was picked from group 4 for the reasons in the next section. The other options remain valid fallbacks if NiceGUI stops fitting.

## NiceGUI Mobile Strengths

Recording these alongside the caveats so the picture is balanced:

- Built on Quasar (Vue component lib), so buttons, inputs, cards, and dialogs are responsive and touch-sized by default.
- WebSocket reactivity keeps the phone in sync with server state without us wiring anything.
- Supports "Add to Home Screen" for a near-app feel, even without a full PWA install path.
- Dark mode, rotation handling, and basic touch gestures on supported components work out of the box.

Where it gets rough on mobile:

- Layout control is coarser than hand-rolled CSS. Dense control-room-style panels on a small phone screen often need Tailwind/Quasar utility classes anyway, which erodes some of the "pure Python" appeal.
- No native gestures beyond what Quasar exposes. No haptics. No real offline mode.
- Long-lived sessions on phones are subject to the iOS/WebKit issues captured later in this doc.

## Current Recommendation

If the next step is "get Control Room onto a phone quickly," `NiceGUI` is the leading candidate.

Why:

- it keeps almost all implementation in Python
- it already provides a browser UI plus realtime server/client updates
- it fits the current prototype scope better than building and maintaining a separate JavaScript app

If the project later decides the web UI is becoming a long-lived primary surface, re-evaluate a cleaner server/client split then. That future concern is out of current scope.

## NiceGUI Suitability

NiceGUI appears suitable for the intended interaction model:

- live status panels
- live log streaming
- command dispatch
- cancel actions
- replay controls

Its built-in realtime channel means we would not start by designing our own raw WebSocket layer if we pick NiceGUI. NiceGUI already handles browser/server synchronization internally.

## iPhone Safari / HTTP Caveat

There is a repo-specific caveat for the current NiceGUI line on iPhone Safari.

Relevant finding:

- NiceGUI issue `#5802` reports that on iOS Safari with NiceGUI `3.7.1`, a minimal app served over plain `http://<LAN-IP>:<port>` reloads repeatedly instead of staying connected.
- The issue report attributes this to the client handshake using `crypto.randomUUID()` in a context that iOS Safari treats as insecure for LAN HTTP.
- The report also states that older NiceGUI versions (`2.9.0` and `2.23.3`) worked on the same device/setup.

Source:

- <https://github.com/zauberzeug/nicegui/issues/5802>

Working interpretation:

- this is a real risk for a NiceGUI-on-iPhone-over-LAN prototype
- the problem is not "Safari cannot display HTTP pages"
- the problem is "NiceGUI v3 currently appears to depend on a browser capability that fails in this insecure-context path on iOS Safari"

## What This Means For Other Stacks

This does not automatically mean every custom web stack would fail the same way.

More precise conclusion:

- plain HTTP plus normal browser traffic is still allowed on iPhone Safari
- a custom stack using basic HTTP requests plus plain WebSocket traffic would not necessarily reproduce the NiceGUI bug
- the failure class appears when the framework or app depends on secure-context-only browser APIs while running from plain `http://<LAN-IP>`

So:

- this is partly an iOS Safari / WebKit secure-context issue
- but the exact repeated-reload failure is still framework-specific unless our own frontend makes the same kind of API choice

## Practical Decision Point

If we prototype with NiceGUI and want iPhone Safari support, plan on HTTPS rather than assuming plain LAN HTTP is enough.

If we build a tiny custom frontend instead, plain HTTP plus WebSocket may still work for the current scope, but HTTPS remains the safer long-term default once mobile Safari is in the loop.

## Follow-Up: Broader iOS / WebKit Caveats

A second pass of research clarified which mobile pain points are framework-specific to NiceGUI versus universal WebKit/iOS behavior. This matters because the answer changes whether switching frameworks would actually fix anything.

Universal WebKit/iOS behavior, hits any WebSocket-based web app:

- Backgrounding the Safari tab kills the WebSocket connection. State-bearing pages re-initialize on return.
- Locking the screen kills the WebSocket. After unlock, the JS side often still reports the socket as `open` while it is actually dead, with no `close` or `error` event fired. This is a documented WebKit behavior, not a NiceGUI bug.
- Service Workers (and therefore any installable PWA) require HTTPS unconditionally. There is no plain-HTTP path to a real PWA install on iOS.

NiceGUI-specific on top of the above:

- Issue `#5802`: plain-HTTP LAN access reloads repeatedly on iOS Safari because the v3 handshake uses `crypto.randomUUID()`, which is a secure-context-only API.
- Issue `#5468`: reports that NiceGUI apps can become unresponsive on iOS Safari after the first successful connection, with subsequent reconnect attempts failing until a manual refresh or cache clear.

Sources:

- <https://github.com/zauberzeug/nicegui/issues/5802>
- <https://github.com/zauberzeug/nicegui/issues/5468>

Practical takeaway:

- Switching away from NiceGUI removes the repeated-reload bug and the post-reconnect unresponsiveness, but does not remove the universal iOS behaviors (background kill, screen-lock kill, fake-open socket).
- Any stack we pick should assume the WebSocket will silently die on mobile and should be able to recover without user intervention beyond an occasional refresh.
- HTTPS remains the safer default for any iPhone-in-the-loop scenario, even when not strictly required by the chosen stack.

## Interaction Transport Shape (Non-NiceGUI Path)

If we end up not using NiceGUI and build the surface ourselves, the suggested split is:

- **Commands, cancel, replay: HTTP POST endpoints.** Addressable, easy to log, easy to script with `curl`, easy to retry. Each action is a discrete request with a clear status code.
- **Live logs and panel/state updates: WebSocket, server to client.** One persistent channel for log lines and another (or a tagged stream) for state diffs. The client only consumes; it does not send commands over the socket.

Why this split:

- Keeps the command surface debuggable and replayable from outside the browser.
- Keeps the WebSocket layer simple (one direction, no command routing) so reconnect logic only has to re-subscribe, not replay in-flight commands.
- Plays well with the universal iOS WebSocket-death problem: a dropped socket only loses the live feed, never an in-flight command.

If we stay on NiceGUI this section does not apply directly, because NiceGUI's realtime channel already covers both directions internally.

## Deferred Implementation Shape

Before any web UI is added, the likely minimum internal refactor is:

1. separate Control Room state/actions from the current Textual rendering layer
2. keep the control logic reusable from either Textual or web UI
3. add the web UI as a thin surface over that shared logic

That is the smallest change that preserves the current app while enabling a phone UI.
