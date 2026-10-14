# Readability update — October 2026

This package replaces the prior catalogue reader/PDF version that appeared too small and faint at normal browser fit size.

## What changed
- Increased contrast and edge definition modestly across the final 31 page rasters.
- Saved the edited page images at high JPEG quality to reduce soft-looking text edges.
- Increased the browser reader's page viewing height so more of the available screen is used.
- Added page zoom controls (fit, 125%, and 150%), image-click zoom/reset, and full-screen viewing.
- Added keyboard controls: Left/Right to change page, + / = to zoom in, - to zoom out, and F for full screen.
- Regenerated the 31-page A4 landscape PDF and preserved its page bookmarks.

## How to test the browser reader
1. Extract the entire ZIP folder; do not open or upload `index.html` by itself.
2. Open `index.html` in a modern browser, or upload the complete folder to hosting while preserving its relative paths.
3. Use **Zoom page** or click a page to magnify fine text; click a magnified page to return to fit. Use the full-screen button for the largest view.
4. Open the PDF when printing or when preferred PDF-reader zoom controls are available.

## Important source limitation
The page artwork is raster-based. Contrast and sharpening improve its appearance, and zoom makes the small details easier to inspect, but these operations cannot recreate vector text that was not present in the generated artwork. Before mass printing, inspect small model specifications at 150–200% and replace any text that is not legible or is not confirmed against LevTech's current product data.
