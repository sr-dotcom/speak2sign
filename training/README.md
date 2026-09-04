# Training (Kaggle, or a local CUDA GPU)

Either works; both are free. The deployed app never sees any of this. Results record the device used.

## Local GPU (developer's RTX 4080, used for the first run)

```bash
python -m venv .venv-train
.venv-train/Scripts/pip install torch --index-url https://download.pytorch.org/whl/cu128
.venv-train/Scripts/pip install -r requirements-train.txt
.venv-train/Scripts/python training/train_t5_gloss.py --limit 2000 --epochs 0.2 --out spike_out/t5_smoke   # 2 min smoke test
.venv-train/Scripts/python training/train_t5_gloss.py --epochs 3 --out spike_out/t5_gloss              # ~10-20 min
.venv-train/Scripts/python training/export_ct2.py --best spike_out/t5_gloss/best --out models/t5_gloss_ct2
```

## Kaggle

1. New Kaggle notebook, GPU on (P100 or T4). Upload `train_t5_gloss.py`, `export_ct2.py`, `requirements-train.txt`.
2. `!pip install -q -r requirements-train.txt`
3. `!python train_t5_gloss.py --epochs 3 --out /kaggle/working/t5_gloss` (about 1–2 GPU hours). Smoke test first with `--limit 2000 --epochs 0.2`.
4. `!python export_ct2.py --best /kaggle/working/t5_gloss/best --out /kaggle/working/t5_gloss_ct2`
5. Download `t5_gloss_ct2.zip` and `t5_gloss/results.json`. Commit `results.json` to `training/results/`. Attach the zip to a GitHub Release and set `T5_RELEASE_URL` in Community Cloud secrets (or unzip into `models/t5_gloss_ct2/` locally).
6. Locally: `python scripts/measure_rss.py` and note the spike-3 numbers in `docs/research/spikes.md`.
