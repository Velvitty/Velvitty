# Profile artwork

Rebuild all twenty desktop and mobile SVGs with Python 3:

```sh
python tools/profile/build.py
```

The build uses only the standard library. `latin-glyphs.json` contains outlined
Noto Sans and DejaVu Sans Mono subsets; their notices are in `FONT-LICENSES.txt`.
Korean outlines and the continuous Möbius geometry are reused from
`assets/studio/`, so keep those source assets when rebuilding.

The palette uses pearl pink `#ffc8e4`, sky `#b9e8ff`, and cream `#ffe5a8`
highlights over indigo, violet, and blue light fields. The Möbius surface has
white highlights, coloured reflections, and a translucent lighting overlay;
the overlay must not desaturate the material into grey. Text is outlined for consistent
rendering without font downloads. README alt text and the complete Markdown
principles remain available to screen readers and search.

The SVGs run as images, with no JavaScript or remote dependencies. Project
motion uses visible preparation, deep compression, accelerated release,
overshoot, and a short settle. The movement is composed around each tool's
function, with no unrelated bouncing ornaments.

| Artwork | Cycle | Visible action |
| --- | --- | --- |
| Illustracy | 2.6 s | Four planes compress to 36% height, then open across 200 px. |
| Posity | 2.4 s | 70 px of film advance/recoil and a full-width development scan. |
| Chordity | 1.2 s per bar | Four simultaneous 25 px key presses, body compression, harmonic release. |
| Analog Soul | 1.8 s | Waveform amplitude contracts to 12%, then expands to 158%. |
| Upscaly | 2.7 s | The frame contracts to 44% width, then opens to 112% and settles. |
| Film Filter Studio | 2.8 s | Iris blades travel 26 px and turn 36 degrees from closure to overshoot. |

Chordity keeps its four chords, simultaneous
four-note strikes, and 1.2-second bars. Motion is illustrative, not an app
screenshot or a performance measurement.

`prefers-reduced-motion: reduce` stops CSS motion and switches the Möbius
SMIL groups to their existing static counterparts. `<picture>` selects the
portrait artwork at viewports up to 640 px. The project cards use full width
so the mobile artwork and titles do not shrink into two narrow columns.

When changing this artwork, check both image variants, the full README in
light and dark themes, image links, SVG IDs and references, and all twenty
principles against the source text. Keep headings and descriptions outside
the images as Markdown where they need to be searchable or expandable.
