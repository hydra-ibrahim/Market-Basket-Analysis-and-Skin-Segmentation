// Single source of truth for the backend URL — every page loads this file first.
//
// Auto-detects whether the page is being viewed locally (opened directly as a file, or served from
// localhost/127.0.0.1 by a local dev server) versus hosted (e.g. GitHub Pages) — and points at the
// matching backend, so a local clone always talks to your local `runserver` and the public copy always
// talks to your deployed backend. Nothing to remember to toggle either direction.
//
// The one thing to edit: replace the fallback URL below with your actual deployed backend's URL once you
// have one. Everything else here is generic detection logic, not something to change per-clone.
const API_BASE_URL = (
    location.protocol === 'file:' ||
    location.hostname === 'localhost' ||
    location.hostname === '127.0.0.1'
) ? 'http://127.0.0.1:8000' : 'https://market-basket-analysis-and-skin.onrender.com';

