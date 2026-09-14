# The Gemini API key, from the command line

Set up on 14 September 2026 against Jonathan's **personal** Google account,
`j0nathanjayes@gmail.com`, not the Nexer one. Every command below passes
`--account` explicitly so the default gcloud configuration, which is signed in
as the work account, is never touched.

## What exists now

| Thing | Value |
|---|---|
| Project | `gen-lang-client-0436883470` ("Gemini API") |
| Billing account | `01A98E-E5B1F9-72F2F4` ("Cabri"), open |
| API | `generativelanguage.googleapis.com`, already enabled |
| Key | display name `bananarama-slides`, restricted to that one API |
| Where the key lives | `.env` at the root of `slides/` and of `ai-education/`, both gitignored |

`.env` holds one line:

```
GEMINI_API_KEY=AIza...
```

`ellmer`, and so bananarama, reads `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
`GOOGLE_API_KEY` wins if both are set.

## Making another key

```bash
A=j0nathanjayes@gmail.com
P=gen-lang-client-0436883470

gcloud services api-keys create --project=$P --account=$A \
  --display-name="bananarama-slides" \
  --api-target=service=generativelanguage.googleapis.com \
  --format="value(response.keyString)"
```

Restricting the key to `generativelanguage.googleapis.com` is not optional
housekeeping: the Gemini API rejects unrestricted standard keys.

Check the key before trusting it. This lists the models it can actually reach:

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$KEY&pageSize=200" \
  | grep -o '"name": "models/[^"]*image[^"]*"'
```

As of September 2026 that returns `gemini-3.1-flash-image`,
`gemini-3.1-flash-image-preview`, `gemini-3.1-flash-lite-image`,
`gemini-3-pro-image` and `gemini-2.5-flash-image`.

## Rotating it

Create a new key with the commands above, replace the line in both `.env`
files, then delete the old one:

```bash
gcloud services api-keys list --project=$P --account=$A --format="table(displayName,uid)"
gcloud services api-keys delete projects/$P/locations/global/keys/<uid> --account=$A
```

## Why not a project of its own

A project called `slide-illustrations` was created for exactly this and could
not be billed: every one of the three open billing accounts on the personal
account returns

```
Cloud billing quota exceeded: billingAccounts/...
```

which is a cap on how many projects one billing account may carry, not a
spending limit. Image models have no free tier, so an unbilled project is
useless here. The empty `slide-illustrations` project is still there; either
delete it, or ask Google to raise the billing quota through the link in that
error and then move the key into it.

## Watching the spend

```bash
gcloud billing accounts describe 01A98E-E5B1F9-72F2F4 --account=$A
```

For actual figures, the billing console is the only real answer:
<https://console.cloud.google.com/billing/01A98E-E5B1F9-72F2F4>. bananarama
also prints the cost of every run, which is the number that matters while you
are iterating.

## No GitHub secret

Considered and skipped. A GitHub Actions secret cannot be read back out, and
nothing generates images in CI: the PNGs are committed, so the site builds
without a key. The `.env` files are the only copy, and the key is recreatable
from this file in about a minute.
