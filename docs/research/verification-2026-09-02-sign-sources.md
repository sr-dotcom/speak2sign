# ASL clip-source licensing audit (verified 2026-09-02)

Produced by the ML/licensing research pass for `docs/00-execution-plan.md`. All quotes are from pages fetched on 2026-09-02 unless marked UNVERIFIED.

## 1. Clip / data sources

| # | Resource | URL fetched | Contents | Licence (quoted) | Redistribute clips in a public web app? | Bulk / API |
|---|---|---|---|---|---|---|
| 1 | **ASL Signbank** | https://aslsignbank.com/about/copyright/ and /about/conditions/ (the haskins.yale.edu host now serves a cert for aslsignbank.com) | 3,702 signs, 2,848 publicly browsable (per the Hamburg LR compendium mirror); video per sign | "This work is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License." Required citation: "Julie A. Hochgesang, Onno Crasborn, and Diane Lillo-Martin. (2017-2026). ASL Signbank. https://aslsignbank.com." | **YES** (non-commercial, attribution, share-alike). Conditions page: users "may link directly to entries, download compressed versions, or request high-quality files from Julie Hochgesang"; "add a direct weblink when you share the video"; do not use draft (non-teal-background) videos. | No API / bulk export; ELAN ECV link only; HQ files by request |
| 2 | **ASL Citizen** (Microsoft) | https://www.microsoft.com/en-us/research/project/asl-citizen/dataset-license/ | ~84k videos, 2.7k signs | §1(c): "you may use and modify the data, but your use and modification must be consistent with the consent under which the data was provided and/or gathered and **you may not distribute the data or your modifications to the data**." §2(e) forbids to "share, publish, distribute or lend the Materials, provide the Materials as a stand-alone hosted solution for others to use". "solely for non-commercial, non-revenue generating, research purposes". | **NO.** Hosting clips publicly = distribution. Training a model on it is fine. | Yes (zip) |
| 3 | **WLASL** | https://github.com/dxli94/WLASL, https://dxli94.github.io/WLASL/ | 2,000 glosses; videos **not hosted** — JSON of URLs + downloader | "Licensed under the Computational Use of Data Agreement (C-UDA)." README: "All the WLASL data is intended for academic and computational use only. No commercial usage is allowed." C-UDA 1.0: "You agree that you will use the Data solely for Computational Use". | **NO.** Displaying clips to humans is not "Computational Use", and the videos are third-party. | Dead links: "Videos can dissapear over time due to expired urls" |
| 4 | **Sem-Lex** | https://github.com/leekezar/SemLex, https://arxiv.org/abs/2310.00196 | 91,148 isolated-sign videos, 3,149 signs, 41 deaf signers | **Gated**: "Please read and agree to the terms of use to access the download links" (Google Form). Code Apache-2.0. Data terms inside the form, not fetchable. | **UNCLEAR → treat as NO** | Form-gated |
| 5 | **ASL-LEX** | https://asl-lex.org/, /download.html | 2,723 signs, 60+ properties; videos online only | "The ASL-LEX database and the ASL-LEX visualization (excluding sign reference videos) are licensed under ... CC BY-NC 4.0." Videos "cannot be 'saved, displayed, or otherwise used for any other purpose without explicit permission.'" | **NO for videos.** YES for the CSV (cite Sehyr et al. 2021, Caselli et al. 2017). | CSV |
| 6 | **Lifeprint / ASLU** | https://www.lifeprint.com/asl101/pages-layout/permission.htm | Dictionary pages | "You do not have permission to use ASLU materials to make, apps of any kind (web, phone, or any other format accessible to the public)." "Do not copy nor embed Lifeprint or other ASLU-related images or videos in your website." | **NO** | None |
| 7 | **Spreadthesign** | Host refused connection 3×; Wikipedia used | 610,000+ videos | Wikipedia: "Produced contents and software are published under proprietary licences." | **NO** (wording UNVERIFIED) | None |
| 8 | **Handspeak** | https://www.handspeak.com/info/index.php?info=terms | Dictionary | "Users may not reproduce, republish, distribute, or otherwise use any content from the Site without prior written permission" + explicit no-AI/ML clause | **NO** | None |
| 9 | **How2Sign** | https://how2sign.github.io/ | 80+ h continuous ASL sentences | "Creative Commons Attribution-NonCommercial 4.0 International License" | YES in principle, but continuous signing; no isolated-sign index | Drive |
| 10a | **CATS "The ASL Dictionary"** (Georgia Tech / Atlanta Area School for the Deaf, Harley Hamilton) | https://archive.org/details/actASL; archive.org/advancedsearch.php?q=creator:("Center for Accessible Technology in Sign") | **24,682 items**, each an isolated ASL sign video (MP4, ~1–2 MB) | Rights field: **"Public Domain"** on every sampled item (7 of 7) | **YES** — strongest option. Attribution recommended. | Yes — advancedsearch JSON + per-item download URLs (https://archive.org/download/<id>/) |
| 10b | **Wikimedia Commons – ASL letters** | https://commons.wikimedia.org/wiki/Category:ASL_letters, File:Sign_language_A.svg | 29 files: "Sign language A.svg" … "Z.svg" | A.svg: "Public Domain", author wpclipart.com | **YES** (check each letter) | Commons API |
| 10c | Wikimedia Commons – Videos in ASL | Category:Videos_in_American_Sign_Language | 161 continuous interpreted speeches (US gov) | Per file | Not isolated signs | — |
| 10d | ASLLRP Sign Bank (BU) | https://www.bu.edu/asllrp/SignStream/3/signbank-lic.html | Sign bank | "can be used only for research and education purposes"; "cannot be redistributed without permission." | **NO** | — |
| 10e | Signing Savvy | https://www.signingsavvy.com/termsofservice | Commercial dictionary | "You may not embed our content into your own product or site in any way" | **NO** | — |

## 2. Avatar / synthetic options

| Option | URL | Licence | Maintained? | Browser, free? | Validated ASL? |
|---|---|---|---|---|---|
| CWASA (successor to JASigning) | https://vh.cmp.uea.ac.uk/index.php/CWA_Signing_Avatars, /CWASA_Conditions_of_Use | "The CWASA software is Copyright UEA (2005-2026)." Example pages CC BY-SA; software "must be used without modification, on terms equivalent to Creative Commons BY-ND." | Page last modified 2024-05-19; JASigning deprecated 2021 | Yes, WebGL, loaded unmodified from UEA server | **Synthetic**; no ASL lexicon ships with it |
| sign.mt / sign/translate | https://github.com/sign/translate | CC BY-NC-SA 4.0 | Active | Yes | **Synthetic** |
| MediaPipe Holistic Landmarker | https://developers.google.com/edge/mediapipe/solutions/vision/holistic_landmarker | Apache-2.0 | Docs updated 2026-08-19 | Yes, on-device | Keypoints inherit the source clip's validity and licence |
| sign-language-processing/pose (pose-format) | https://github.com/sign-language-processing/pose | MIT | Recency unclear | `pose-viewer` package UNVERIFIED (npm 403) | n/a |

## 3. Ranked recommendation for redistribution in a public non-commercial academic app

1. **CATS "The ASL Dictionary" on archive.org — Public Domain, ~24.7k isolated-sign MP4s, scriptable bulk download.** Verify the `rights` field per item on ingest and check signer quality.
2. **ASL Signbank — CC BY-NC-SA 4.0, ~2.8k public signs, linguist-curated.** Permits downloading compressed videos and re-sharing with a direct weblink. Obligations: non-commercial, exact citation string, share-alike on derivatives, skip draft videos, no bulk endpoint.
3. How2Sign — CC BY-NC 4.0, continuous only.
4. ASL-LEX CSV — CC BY-NC 4.0 metadata only, never its videos.
5. Everything else is out for redistribution. ASL Citizen and WLASL remain usable for training a recogniser server-side.

## Fingerspelling fallback

| Source | Licence | Notes |
|---|---|---|
| Wikimedia Commons `Sign language A.svg` … `Z.svg` | Public Domain (A confirmed; series assumed) | Clean SVG line drawings |
| CATS archive.org letter items | Public Domain | Not verified that all 26 exist |
| ASL Signbank letter entries | CC BY-NC-SA 4.0 | Real-signer video per letter |
| Lifeprint fingerspelling images | **NO** — app ban | — |

## UNVERIFIED

- Spreadthesign terms (site unreachable).
- Sem-Lex data licence (inside the Google Form).
- ASL Signbank public-video count (2,848 from a mirror).
- CWASA open-use sentence seen only in a search snippet.
- `pose-viewer` browser component existence/licence.
- Wikimedia letters B–Z licences per file.
- CATS collection completeness, signer identity, and letter coverage (7 items sampled).
- ASL Citizen video count (from the project page, not the licence page).
