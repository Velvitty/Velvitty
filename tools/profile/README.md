# Profile artwork

Rebuild all twenty desktop and mobile SVGs with Python 3:

```sh
python tools/profile/build.py
```

The build uses only the standard library. `latin-glyphs.json` contains outlined
Noto Sans and DejaVu Sans Mono subsets; their notices are in `FONT-LICENSES.txt`.
Korean outlines and the continuous Möbius geometry are reused from
`assets/studio/`, so keep those source assets when rebuilding.

The palette uses white-pink `#ffeaf2`, white-sky `#e4f4ff`, and white-yellow
`#fff6dc` over a quiet charcoal background. Text is outlined for consistent
rendering without font downloads. README alt text and the complete Markdown
principles remain available to screen readers and search.

The SVGs run as images, with no JavaScript or remote dependencies. Project
motion uses preparation, compression, accelerated release, a small overshoot,
and a long settling interval. Chordity keeps its four chords, simultaneous
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
