# Training (Kaggle only)

1. New Kaggle notebook, GPU on (P100 or T4). Upload `train_t5_gloss.py`, `export_ct2.py`, `requirements-train.txt`.
2. `!pip install -q -r requirements-train.txt`
3. `!python train_t5_gloss.py --epochs 3 --out /kaggle/working/t5_gloss` (about 1–2 GPU hours). Smoke test first with `--limit 2000 --epochs 0.2`.
4. `!python export_ct2.py --best /kaggle/working/t5_gloss/best --out /kaggle/working/t5_gloss_ct2`
5. Download `t5_gloss_ct2.zip` and `t5_gloss/results.json`. Commit `results.json` to `training/results/`. Attach the zip to a GitHub Release and set `T5_RELEASE_URL` in Community Cloud secrets (or unzip into `models/t5_gloss_ct2/` locally).
6. Locally: `python scripts/measure_rss.py` and note the spike-3 numbers in `docs/research/spikes.md`.
