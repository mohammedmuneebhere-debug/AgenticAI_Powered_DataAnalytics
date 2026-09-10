# Twitter/X Web Scraper Experiment

This document records the isolated Twitter/X web-scraper experiment that was
removed from the application code. It is documentation only and is not loaded
by the backend, frontend, agents, or deployment configuration.

## Original goal

Build a scraper that accepts a search query from the frontend and retrieves
publicly rendered X posts without requiring an X API key.

## Changes that were tested

- Added a standalone Playwright scraper module at
  `backend/services/twitter_web_scraper.py`.
- Added a `TwitterWebScraper` class and `scrape_twitter_web` convenience
  wrapper.
- Accepted a query and bounded `max_results` value.
- Extracted post ID, text, author, timestamp, URL, and engagement counts.
- Added Playwright as a backend dependency and required Chromium installation.
- Added optional `X_USERNAME` and `X_PASSWORD` environment variables.
- Tried X login selectors based on the live login page:
  `input[name="username_or_email"]`, `input[name="password"]`, and the
  current Continue/Log in controls.
- Tried persistent Playwright storage state in
  `data/x_storage_state.json`.
- Tried a persistent headed Chromium profile in
  `data/x_browser_profile`.
- Added README and environment-example instructions for the isolated tool.

## Validation and observed behavior

- Python syntax and Pylance diagnostics passed.
- Playwright Chromium installation succeeded.
- Public/headless browsing did not produce usable X search results.
- X redirected automated sessions to its login/onboarding flow.
- Credential-based login did not reliably advance past the X login shell.
- Saved storage state was created but was not accepted by X.
- The persistent headed profile still required manual login and did not
  reliably return search articles in the automated test.
- CAPTCHA, MFA, account verification, and login controls were not bypassed.

## Current repository state

The scraper implementation, Playwright dependency, environment-variable
entries, README instructions, and scraper-specific ignore rules have been
removed from the application. Existing backend routes, frontend code, agent
orchestration, and the X API method were left unchanged.

This file is intentionally standalone so the experiment can be reviewed later
without reintroducing any runtime behavior.
