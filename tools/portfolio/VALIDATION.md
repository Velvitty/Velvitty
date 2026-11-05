# GitHub profile adaptation — 2026-11-05

- Built all six localized READMEs and 144 desktop/mobile SVG assets.
- SVG XML, unique IDs, all local paint/clip/glyph references, and text bounds pass.
- No scripts, foreignObject or external resources in SVG images. Embedded photos
  and the original licensed font outlines render inside ordinary image elements.
- Every README retains eight project links, six language controls and the twenty
  original principles with their rationale. MacGuard is in security.
- Browser preview loaded all 16 images for every locale at 320 CSS pixels.
  Language controls remained on one row. Document width matched viewport width
  at 320, 375, 620, 768 and 1024 CSS pixels, with scrollbar space accounted for.
- Two observed hero frames show different material positions with an identical
  Möbius pose. The exact 720 face clips, affine UV mappings and source lighting
  are retained. The material advances in the original positive-X direction.
- The complete interactive page builds and passes `node check.mjs`: locale
  schemas, 48 localized banners, eight repository destinations, model fidelity,
  30/60/120/144 Hz simulation, fractional interpolation, bounded late-frame
  recovery, pause/drag/hidden-tab resets and release contents.
- Direct `?lang=ko#posity` navigation resolves to the comparison card after the
  initial smooth scroll. End/Home update its slider to 95%/5%. No application
  JavaScript error was observed; browser-extension metadata errors are unrelated.
- Existing `index.html`, `CNAME`, manifest, service worker, offline page and PWA
  bundle are excluded from the change. The full experience is a new subdirectory
  at `/portfolio/`; no private Sites identity, credentials or hosting manifest
  are included in the public commit.

The local README preview models GitHub image sizing and picture source behavior;
GitHub's rendered page and Pages deployment are verified after the atomic commit.
SVG animation timing follows browser/display capabilities and is not a 120 FPS
hardware guarantee. Interactive controls run on the linked full website, not
inside GitHub's Markdown renderer.
