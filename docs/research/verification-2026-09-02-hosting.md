# Free-tier verification report — hosting, storage, CI (verified 2026-09-02)

Produced by the DevOps/cost research pass for `docs/00-execution-plan.md`. All numbers were read from the linked official pages on 2026-09-02. Third-party/community sources are labelled as such.

## 1. Streamlit Community Cloud

| Item | Value | Source quote |
|---|---|---|
| URL fetched | https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app, …/status, …/share-your-app, https://streamlit.io/cloud | |
| RAM | 690 MB min, **2.7 GB max** | "Memory: 690MB minimum, 2.7GBs maximum" |
| CPU | 0.078–2 cores | "CPU: 0.078 cores minimum, 2 cores maximum" |
| Storage | up to 50 GB | "Storage: No minimum, 50GB maximum" |
| Sleep | **12 h** no traffic | "All apps without traffic for 12 hours go to sleep." |
| Repo requirement | GitHub repo, public by default; **one private app** per workspace | "You are only allowed one private app at a time." / marketing page: "Public apps only" |
| App count | UNVERIFIED (no number on any docs page fetched) | |
| HTTPS / domain | HTTPS on `<subdomain>.streamlit.app`; custom subdomain 6–63 chars; no custom domain | "Enter a new, custom subdomain between 6 and 63 characters" |
| Cost / card | "Totally free"; no card mentioned anywhere | |
| Demo-relevant | Hosted in US only; GitHub redeploys rate-limited to 5/min; cold start after 12 h idle | |

## 2. Hugging Face Spaces (free CPU tier) — major change

| Item | Value | Source quote |
|---|---|---|
| URL fetched | https://huggingface.co/docs/hub/spaces-overview, …/spaces-gpus, …/spaces-zerogpu, …/spaces-storage, …/spaces-custom-domain, https://huggingface.co/pricing | |
| CPU Basic hardware | 2 vCPU, 16 GB RAM, 50 GB ephemeral disk | "Each Spaces environment is limited to 16GB RAM, 2 CPU cores and 50GB of (not persistent) disk space" |
| **Paid-plan gate** | **Gradio/Docker Spaces now require PRO ($9/mo) or Team/Enterprise.** Static Spaces free. | "Gradio and Docker Spaces run on compute and require a paid plan to create… Free personal accounts in good standing can still host up to 2 Gradio Spaces running on ZeroGPU." |
| Free escape hatch | Up to **2 ZeroGPU Gradio Spaces** for free accounts (verified email, account >30 days old); Gradio SDK only; 5 min/day GPU quota per visitor account | "accounts in good standing (verified email, account older than 30 days) can host up to 2 ZeroGPU Spaces for free" |
| Sleep | **48 h** inactivity on cpu-basic | "it will go to sleep if inactive for more than a set time (currently, 48 hours)" |
| Streamlit SDK | Not listed any more: "The Hub offers three SDK options: Gradio, Docker and static HTML." | |
| Persistent storage | Ephemeral; Storage Buckets billed at "$12 /TB/mo" | |
| Custom domain | PRO/Team/Enterprise only | |

Community confirmation: https://discuss.huggingface.co/t/official-community-complaint-revert-free-cpu-basic-spaces-and-remove-anti-developer-sdk-restrictions/177703 and https://discuss.huggingface.co/t/new-free-accounts-cannot-create-cpu-basic-gradio-spaces-only-zerogpu-available/177629

## 3. Cloudflare R2

| Item | Value | Source quote |
|---|---|---|
| URL fetched | https://developers.cloudflare.com/r2/pricing/, …/r2/buckets/public-buckets/, …/r2/platform/limits/, …/r2/get-started/ | |
| Storage | 10 GB-month/month (Standard class only) | "10 GB-month / month" |
| Class A / B | 1 M / 10 M requests per month | |
| Egress | Free | "Egress: Free" |
| Public access | `r2.dev` subdomain is rate-limited, dev-only; custom domain requires a zone in the same Cloudflare account | "Public access through `r2.dev` subdomains is rate-limited and should only be used for development purposes." / "The domain being used must have been added as a zone in the same account as the R2 bucket." |
| Card | Docs: "Complete the checkout flow to add an R2 subscription to your account." Payment-method requirement confirmed only via community (https://community.cloudflare.com/t/if-i-want-to-use-cloudflare-r2-i-have-to-link-a-payment-method-i-suggest-not-doin/887578) → PARTIALLY VERIFIED |

## 4. Cloudflare Pages

| Item | Value | Source quote |
|---|---|---|
| URL fetched | https://developers.cloudflare.com/pages/platform/limits/, …/pages/functions/pricing/, …/workers/platform/pricing/ | |
| Builds | 500/month, 1 concurrent, 20 min timeout | "500 deploys per month on the Free plan" |
| Files | 20,000 files/site; 25 MiB max per asset | "maximum file size for a single Cloudflare Pages site asset is 25 MiB" |
| Bandwidth | No GB number published; static requests "free and unlimited" | |
| Functions | 100,000 req/day shared with Workers Free; 10 ms CPU/invocation | |

## 5. GitHub (Actions / Pages / LFS)

| Item | Value | Source quote |
|---|---|---|
| URLs fetched | https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-actions, …/github-pages-limits, …/about-storage-and-bandwidth-usage, …/about-git-large-file-storage, …/githubs-plans | |
| Actions, public repo | Free, standard runners | "The use of standard GitHub-hosted runners is free: In public repositories" |
| Actions, private (Free plan) | 2,000 min/month, 500 MB artifact storage, 10 GB cache/repo | |
| Pages | Public repos on GitHub Free; site ≤ 1 GB; **soft 100 GB/month bandwidth**; soft 10 builds/h; no commercial use | "Published GitHub Pages sites may be no larger than 1 GB." / "soft bandwidth limit of 100 GB per month" |
| LFS | 10 GiB storage + 10 GiB bandwidth/month on Free; metered overage; 2 GB per file on Free | |
| Demo-relevant | Pages does not serve LFS-stored objects — commit clips as plain files (< 100 MB each) | |

## 6. Render and Fly.io

| Item | Render | Fly.io |
|---|---|---|
| URL fetched | https://render.com/docs/free, https://render.com/docs/compute-plans | https://fly.io/docs/about/pricing/, …/billing/, …/free-trial/, …/discontinued-plans/ |
| RAM / CPU | Free instance: **512 MB, 0.1 CPU** | Trial only |
| Sleep | "spins down a Free web service that goes 15 minutes without receiving any inbound traffic" | machines auto-stop after 5 min in trial |
| Hours | "750 Free instance hours to each workspace per calendar month" | **No free tier.** Trial = "2 hours of machine runtime or 7 days of access, whichever comes first"; legacy free allowances ended 2024-10-07 |
| Card | not required for Free | "require an active, valid credit card on file for most Fly.io accounts" |

## 7. Vercel Hobby / Netlify Free (brief)

Vercel Hobby: "100 GB / month included" transfer; 1M invocations; "non-commercial, personal use only"; serverless only. Netlify Free: 300 credits/month, "20 credits per GB"; projects paused when credits run out. Neither can host a resident 1 GB Python process.

## 8. Backblaze B2 (brief)

"First 10GB storage is always free."; "Free egress up to 3x" average monthly storage; card requirement for the free tier UNVERIFIED. Needs a CDN in front for sane public URLs.

## Recommendation (as delivered)

Simplest zero-cost setup: one public GitHub repo deployed to Streamlit Community Cloud, with the MP4 clips committed in the repo (each file < 100 MB, repo comfortably < 1 GB). Community Cloud is the only mainstream free host verified today that gives a Python process more than 1 GB RAM with no card, no paid gate, and HTTPS. Runner-up: a Gradio app on a Hugging Face ZeroGPU Space (2 free per personal account older than 30 days, Gradio SDK only, 16 GB RAM, sleeps after 48 h). Render Free (512 MB) only works with a model under ~400 MB resident; Fly.io no longer has a free tier.

## UNVERIFIED

- Community Cloud maximum apps per account.
- Community Cloud "Public apps only" (marketing) vs docs "one private app at a time"; docs treated as authoritative.
- Cloudflare R2 credit-card requirement (community threads only).
- Cloudflare Pages bandwidth figure.
- Backblaze B2 card requirement for the free tier.
- GitHub Pages custom-domain/HTTPS support and 100 MB per-file push limit (long-standing docs, not re-fetched today).
- Whether pre-existing free HF CPU Basic Spaces stay alive; the pricing page's "CPU Basic … FREE" row conflicts with the overview's paid-plan gate.
- Vercel Hobby monthly build-minute quota.
