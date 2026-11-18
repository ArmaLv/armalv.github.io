# ✦ Enter the Drift — About-Me site

A single-page **About Me** for GitHub Pages, with a theme that drifts between
sci-fi, nature, and a novel you don't want to close. Separate HTML, CSS, and JS,
plus a small Python tool that turns any GitHub repo link into a project card.

## Structure

```
.
├── index.html              # the page (markup only)
├── css/
│   └── style.css           # all styling + scroll-reveal animation
├── js/
│   └── main.js             # starfield drift, scroll vine, reveals, project cards
├── data/
│   └── projects.json       # project cards rendered in the "Works" section
├── Assets/
│   ├── branches/           # sakura branch SVGs framing the page (your art)
│   └── leaves/             # individual leaves split from the falling-leaves SVG
└── tools/
    ├── project_generator.py # paste a repo link → writes a card into projects.json
    └── split_leaves.py      # split a falling-leaves SVG into individual leaves
```

## Sakura art

The branches are placed as fixed decorations in `css/style.css` under
`.branch--tl / --tr / --l / --r / --bl / --b` — each anchored off an edge and
`rotate()`/scaled; swap positions or transforms there. The falling leaves are
generated in `initLeaves()` in `js/main.js` from the files in `Assets/leaves/`,
each with a random leaf, size (scale), rotation, and drift.

To re-split the leaves after editing the source art (two groups intentionally
hold two leaves each and stay intact):

```bash
python tools/split_leaves.py Assets/leaves/_source-falling-leaves.svg Assets/leaves
```

## Run it locally

Because the page `fetch`es `data/projects.json`, open it through a tiny local
server (opening the file directly will block the fetch):

```bash
python -m http.server 8000
```

Then visit <http://localhost:8000>.

## Deploy to GitHub Pages

1. Push these files to the **root** of a repo (e.g. `armalv.github.io` for a user
   site, or any repo with Pages enabled).
2. In **Settings → Pages**, set the source to the `main` branch, root folder.
3. Your site goes live at `https://<username>.github.io/`.

## The project generator

Paste a GitHub link (full URL or `owner/repo`) and it reads the repo itself —
name, description, topics/tags, README excerpt, languages, and stars — then
writes a card into `data/projects.json`. No dependencies; standard library only.

```bash
# add / update a project
python tools/project_generator.py https://github.com/ArmaLv/DialogueSystem

# several at once
python tools/project_generator.py ArmaLv/StyTab ArmaLv/DialogueSystem

# see what's stored
python tools/project_generator.py --list

# preview a card without saving
python tools/project_generator.py --dry-run ArmaLv/StyTab

# remove one
python tools/project_generator.py --remove StyTab
```

Running it again for the same repo **updates** that card in place.

### GitHub rate limits

Unauthenticated requests are capped at ~60/hour. To raise the cap, set a token
(no scopes needed for public repos):

```bash
# PowerShell
$env:GITHUB_TOKEN="ghp_xxx"

# bash
export GITHUB_TOKEN=ghp_xxx
```

## Customizing

- **Colors & fonts** — the `:root` variables at the top of `css/style.css`.
- **Sections / text** — edit `index.html` directly; every section is a
  `.chapter`. Add `data-reveal` to any element to give it the scroll-in animation
  (`data-delay="1..n"` staggers it).
- **Background drift** — tune particle count, colors, and speed in `initDrift()`
  inside `js/main.js`. All motion respects `prefers-reduced-motion`.
