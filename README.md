# LevTech Integrated Systems — Final Catalogue 2026

**Final editorial edition: 31 A4-landscape pages**  
Brand line: **Smart. Secure. Reliable.**

This package contains the curated print-ready catalogue, the page artwork used to assemble it, the Python source used to rebuild the PDF with modest contrast/sharpness enhancement, and an offline browser reader with light/dark themes, larger page display, zoom, fullscreen and page navigation.

## Start here

- Open `LevTech_Integrated_Systems_Catalogue_2026.pdf` for the complete final catalogue.
- Open `index.html` in a current desktop browser for the navigable visual reader.
- Run `python build_catalogue.py` to rebuild the print PDF from the selected assets in `source_artwork/`.
- Read `CURATION_NOTES.md` for the editorial decisions and `SERVICE_COVERAGE.md` for the service/product coverage check.

## Contents

- `pages/` — all 31 final page images, numbered in publication order.
- `source_artwork/` — selected source images required by `build_catalogue.py`.
- `original_artwork_archive/high_resolution_available/` — unique high-resolution alternative/generated pages found in the available source ZIPs; images duplicated in `source_artwork/` are not duplicated here. Together, the selected source folder and this archive retain the unique high-resolution artwork that was available.
- `original_artwork_archive/44_page_review_previews/` — all 44 page review JPGs retained for audit/reference. They are rendered previews, not guaranteed to be the original full-resolution generated files. See `source_inventory.csv` for dimensions and paths.
- `catalogue_manifest.json` and `.js` — page titles and descriptions.
- `build_catalogue.py` — reproducible image-page and PDF assembly source.
- `index.html`, `viewer.css`, `viewer.js` — self-contained offline reader source with fit/125%/150% zoom, fullscreen viewing and keyboard navigation.

Some of the earlier individual high-resolution source files were not present in the available source packages (the original page-24 PNG was empty). The 44-page review JPG set is retained for traceability; the final 31-page catalogue uses the curated source artwork and includes every listed LevTech service family.

## Rebuild requirements

Python 3.10 or later, Pillow and ReportLab are required. OpenCV and NumPy are optional; they are used only for cleaning the small legacy year text on the cover.

```bash
python -m pip install -r requirements.txt
python build_catalogue.py
```

The output file is `LevTech_Integrated_Systems_Catalogue_2026.pdf`.

## Readability update

The final page images are contrast- and edge-enhanced and re-saved at high JPEG quality. The browser reader uses more of the available viewport and supports zooming and fullscreen display. Because the design pages are image-led raster artwork, very small embedded product notes are still easiest to read in zoom/fullscreen mode; important final specs should be checked before print.

## Production note

This is an editorial product-and-solutions catalogue. Confirm model availability, exact specifications, warranty terms, subscription fees and approved contact details against current LevTech records before mass printing. Compatibility and functionality may vary by selected model and installation.
