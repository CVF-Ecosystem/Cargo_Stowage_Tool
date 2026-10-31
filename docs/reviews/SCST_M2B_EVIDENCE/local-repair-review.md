# Bounded reviewer-local repairs

Root's first full browser run had21passes/1failure. The old VINAFCO camera test measured the canvas rectangle below the viewport after the new planner panel increased page height; raw mouse coordinates missed the canvas. Root added `canvas.scrollIntoViewIfNeeded()` before measuring. Camera movement/reset/zoom/picking assertions remain unchanged.

Root also added one runtime statement after a successful, revision-checked `applyAutomatic`: on the next animation frame, scroll `.viewer-card` into view. It changes only scroll position, making the newly placed cargo immediately visible. The planner, metadata, geometry, mass, validation and history logic are unchanged. One M2b assertion now checks the canvas is in the viewport after apply.

Sol independently reviewed both changes read-only and accepted their limited boundary: the UI scroll occurs only after validate succeeds and the revision guard passes; optional chaining safely does nothing without a viewer. The test scroll makes an actual mouse drag reach its target without weakening expected camera behavior. Acceptance was conditional on root's fresh build/full suite. Root subsequently built and ran all22browser tests successfully in46.7s.

This is the same objective/design/path-family/authority/effects/commit owner; the failure evidence determines the test fix and M2B-03 owns the user-visible result. No REWORK or scope expansion. Root's runtime contribution is limited to that scroll statement, disclosed separately from the independently reviewed Terra implementation. Backend98tests/restart/8,941oracle assertions remain valid because backend bytes did not change.

Run logs preserve initial failures; trailing blank characters in packaged tool logs are stripped for diff hygiene, with verbatim copies in ignored runtime. Result/error/assertion text is unchanged.
