# Harris Hub 2.0

A free, mobile-friendly personal discovery dashboard with per-item feedback, recommendation history, and direct source links for fetched items.

## Install

Upload the **contents** of this folder to the root of your existing `jharris823/harris-hub` repository, replacing matching files. Include the hidden `.github/workflows/refresh.yml` file. GitHub Pages remains configured to deploy `main` / root. Run Actions → Refresh public headlines → Run workflow.

**Important:** Before replacing files, export your existing browser preferences from Settings and save the JSON backup. This version keeps the existing `hh_*` localStorage keys and supports the original import format. If you already have a working `data/feeds.json`, preserve that existing file rather than replacing it with the empty starter file here.

## What is new

- Dismiss, Already know, Love, Interested, Save, and Undo on sci-fi picks and live headline cards.
- My Library history with restore actions; previously completed or dismissed items are suppressed.
- Feedback stored privately on-device; export/import transfers preferences between devices.
- A refreshed daily homepage that emphasizes actual fetched discoveries over Google search links.
- Public OpenAlex research records with direct DOI/landing-page links, publication dates, and relevance explanations.
- Google/Bing RSS backup sources for other public headlines.

## Honest limits

This version does not yet fetch live comic listings/prices, restaurant reservations, concert tickets, or ski packages. Existing section links for those categories remain navigational rather than verified deals. No AI API, background personalization server, or cross-device sync is included. Feedback improves local display and suppression; it does not alter public server-side discovery. Static curated sci-fi picks are a starter pool, so eventually that pool may be exhausted. The public feed requires internet and may fail due to source restrictions.

Never commit private preference exports to a public repository.


## v2.1 — actionable discovery

- Research: OpenAlex structured scholarly records (authors, dates, DOI/source links, abstracts when provided). The metadata-based relevance explanation is not an AI-generated paper review.
- Comics: **actual listings require eBay developer credentials**. Create GitHub Actions secrets `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`, then add those secrets to the workflow `env` of the Python update step. Without credentials, the section honestly shows no verified listings, not invented deals. Listings may sell or change after refresh.
- The workflow continues using `python update_feeds.py`; no new dependencies. Do not replace existing `data/feeds.json` on upload.
- Feedback and library remain stored in your browser; keep a Settings export as backup.
- OpenAlex API usage may be subject to changing free budgets and throttling.
