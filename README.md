# a4lbum — A4 Photo Album Maker

**Language:** English | [한국어 (Korean)](README.ko.md)

- [Photo folder before (example)](examples/photos/)
- [Photo album after (example)](examples/photos_album.pdf)

Pick a photo folder and get a PDF with **two photos (top and bottom) on each A4 page**. Each photo gets a **note label** with its caption at the top-right corner. Print it, slip the pages into an A4 clear file, and you have an album.

Captions come from the photo file names, and photos go in uncropped at their original quality. iPhone photos (HEIC) and most other image formats are converted automatically, and your original photo files are never changed.

## How to use

Nothing to install. (Windows 10/11)

### 1. Download

1. On this GitHub page, click the green **[Code] → Download ZIP**.
2. Right-click the zip → **Extract All**.

> The `app` folder next to the exe files is part of the program (both exes use it). Do not delete or move it.

### 2. Prepare your photos

Put the photos in one folder and rename each file to the caption you want on its note label (the extension is left out). Example: `Cherry blossom festival.jpg` → "Cherry blossom festival"

- You set the album order in the "Photo order" list in the window (step 3 below).
- Captions of up to 60 characters work best. Longer ones get a smaller font and are then cut short with "…".
- With an odd number of photos, the bottom half of the last page stays empty.
- Example: the album made from the 5 photos in [examples/photos/](examples/photos/) is [examples/photos_album.pdf](examples/photos_album.pdf).

### 3. Make the album

![The album window: pick a photo folder, the photo order list appears, sort it or move photos with the buttons on each row, then press [Make album]](docs/app-window.png)

1. Double-click **`Photo Album Maker (English).exe`**.
   - If a blue "Windows protected your PC" box appears, click **More info → Run anyway**.
2. Next to "Photo folder", click **[Browse…]** and pick your photo folder.
   - You can also drag the photo folder onto the exe.
3. Check the order in the "Photo order" list and change it if needed. Photos go into the album **exactly in the listed order**: top, bottom, then the next page.
   - **Sort**: "By name" (default; leading numbers compare by value, `1_` → `2_` → `10_`), "By date created", "By date modified", "By date taken". Date sorts put the oldest first; tick **Reverse (descending)** to flip the order.
   - With a date sort, each row shows that date.
   - "Date taken" is the time the camera or phone recorded in the photo. Photos without it (screenshots, images saved by editing apps, etc.) use their date modified instead and get a **⚠** before the date. When any row has ⚠, its meaning is shown to the right of the sort controls.
   - Use **[▲] [▼]** on each row to move a photo one step, or **[To top] [To bottom]** to move it all the way. Once you press any of them, the sort shows **"Custom"**. Choosing a sort again discards your manual order.
   - **Double-click a file name** to rename the photo file right there (the extension stays). Press Enter to rename, Esc to cancel. The note label comes from the new name.
   - **Hover over a file name** to see a small preview of the photo.
4. Tick **Drop a leading "number_" from file names in note labels** if needed. Hover over it to see what it does.
5. Press **[Make album]**, and when it is done, check it with **[Open PDF]**.

The order and checkboxes are not saved when you close the window.

The PDF is saved **right outside** the photo folder as `<folder name>_album.pdf` (e.g. `Photos\2026_Trip` → `Photos\2026_Trip_album.pdf`). To save it somewhere else, use [Browse…] next to "Save PDF as".

A `Warning:` line in the Result area means something is wrong with that photo (a broken file, an empty caption, low resolution, etc.). The PDF is still made with the other photos.

### 4. Print

In your PDF viewer, print on **A4 paper** at **"Actual size" (100%)**. Single- and double-sided both work.

## For developers

Run from source with Python 3.10 or later. The result is the same as the exe.

```powershell
pip install -r requirements-dev.txt          # runtime + test dependencies

python scripts/album_app.py                  # the window (--english: English window)
python scripts/make_album.py "C:\Photos\2026_Trip" [-o out.pdf] [--font font.ttf]   # command line (Korean output)
python -m pytest                             # tests
```

- In Claude Code, run `/album C:\Photos\2026_Trip`.
- The command line and `/album` always use name order and drop a leading `number_` from captions. The order list and the "number_" checkbox exist only in the window.
- After changing the code, run `powershell -ExecutionPolicy Bypass -File build_portable.ps1` to rebuild `앨범 만들기 (한국어).exe`, `Photo Album Maker (English).exe` and `app\`, and commit them together. The two exes are copies of one build; an exe name containing `(English)` makes it run in English. The build checks that both exes make a real album without Python and leaves the existing exes alone if that fails. At the end, `make_example.ps1` remakes `examples/photos_album.pdf` with the new exe (it can also be run on its own).
- Design documents (Korean): [specs/](specs/)
