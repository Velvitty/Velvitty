# Interactive portfolio and GitHub profile

The self-contained website is served at `https://yeon.at/portfolio/`.
The root `index.html`, domain, and existing PWA implementation remain unchanged.
This is the public GitHub copy of the approved photographic motion edition.

From this directory, run `node build.mjs && node check.mjs`, then copy
`dist/index.html` to `../../portfolio/index.html`. No package installation or
external runtime dependency is needed. The output contains the CSS, JavaScript,
six languages, two photographs, and the exact 720-face Möbius model.

From the repository root, run `python3 tools/profile/portfolio.py` to regenerate
the six READMEs and 144 responsive SVG assets in `assets/portfolio/`.
The existing `python3 tools/profile/build.py` command also selects this edition;
`--legacy` reproduces the previous profile. Locale principles remain in
`tools/profile/locales/`, while short copy, photos and interactive source are here.

GitHub sanitizes page JavaScript and inline styling in Markdown. The profile
therefore uses declarative SVG/CSS previews. Each project image opens the matching
interactive card, with the selected locale and an anchor. Source repository links
remain in the expandable project table. MacGuard is categorized as security.
The 20 original principles and their explanations remain in all six languages.

SVG images are self-contained: embedded JPEG photo derivatives, outlined glyphs
from the existing licensed subsets, and system font fallbacks for newly used
characters. Font notices stay in `tools/profile/FONT-LICENSES*.txt`. Photos are
conceptual examples, not real application processing results. Image provenance
is documented in `assets/README.md`. The original WebP photos remain embedded
at full quality in the interactive HTML.

The profile's Möbius keeps the exact clips, UV affine transforms, lighting,
silhouette and fixed pose from `mobius-reference.svg`. Animated paint servers
move only its material in the original positive-X direction, with a 5.6-second
cycle. Reduced motion switches its material to static paint servers. The full
HTML retains its 120 Hz logical timeline and late-frame interpolation; actual
display frame rate is controlled by the browser and display.

Profile image captions describe opening the live demonstration, rather than
implying that a README image is a working slider. The live page retains the
2px/3px/2px vertical comparison controls, four alternating chevrons offset 7px,
keyboard controls, card press/release/off effects, no audio autoplay, motion
pause, and reduced-motion handling.
