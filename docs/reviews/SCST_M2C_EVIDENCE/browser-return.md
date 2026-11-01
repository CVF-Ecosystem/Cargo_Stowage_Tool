# SCST M2c browser worker return

Focused Playwright run against frozen frontend build `index-D1j1nlxy.js`: **6/6 passed in 32.0 s**. The command ran `m2c.spec.ts` with the repository's Playwright web server and isolated test data; the exact console output is in [m2c-playwright.log](browser/m2c-playwright.log).

The six browser journeys cover:

1. Pin checked A, save it, edit B by exactly 1 g plus X position and yaw, inspect the API and UI field diff, restore A, undo to B, then save B under a new UUID while the saved A remains immutable.
2. Reload, load a saved A as baseline, and verify checked B and its selected cargo remain in place.
3. Load all 1,076 source units, change one unit, confirm 1 CHANGED and 1,075 UNCHANGED, search/filter/page 50 rows, select a B unit, and inspect the mobile 2D fallback with one viewer and no horizontal page overflow.
4. Replace CSV cargo and verify ADDED, REMOVED and CHANGED rows, including that an A-only removed unit has no B selection control.
5. Exercise STALE, delayed compare and network failure; newer B, selection and baseline persist.
6. Exercise delayed saved-baseline and restore responses and a failed restore; newer selection or raw draft persists.

Screenshots: [desktop comparison](browser/compare-desktop.png) and [mobile fallback comparison](browser/compare-mobile-fallback.png). Both were visually inspected. The desktop B edit deliberately creates overlap and is correctly shown as DRAFT with validation issues; the comparison proves exact differences, not a safe stowage plan. The mobile source-list scenario starts with unplaced units, so its 2D fallback shows an empty hold while the comparison covers all units.

Only `tests/browser/m2c.spec.ts` and this M2c browser evidence were created. Existing browser assertions were unchanged. The root reviewer owns the inherited full-suite run and final disposition. These are product/UI and API integration checks; they make no CVF governance or operational safety claim.
