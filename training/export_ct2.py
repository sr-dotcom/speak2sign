"""Export the fine-tuned T5 to CTranslate2 int8 for the torch-free runtime (ADR 0005).

    python export_ct2.py --best /kaggle/working/t5_gloss/best --out /kaggle/working/t5_gloss_ct2

Produces: <out>/model.bin + config + spiece.model (the SentencePiece file the runtime tokenises with),
and <out>.zip for download. Attach the zip to a GitHub Release; the app fetches it on first use.
This script prints the export size. To measure resident memory and latency with the export in place, run
scripts/measure_rss.py from the dev environment (requirements-dev.txt; it also loads whisper, as the app does).
"""
import argparse
import shutil
from pathlib import Path

from ctranslate2.converters import TransformersConverter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--best", required=True)
    ap.add_argument("--out", default="t5_gloss_ct2")
    ap.add_argument("--model", default="google-t5/t5-small", help="the base model the checkpoint was trained from (train_t5_gloss.py --model); used only if spiece.model is missing")
    args = ap.parse_args()
    out = Path(args.out)
    TransformersConverter(args.best).convert(str(out), quantization="int8", force=True)
    spiece = Path(args.best) / "spiece.model"
    if not spiece.exists():  # tokenizer saved as tokenizer.json only: regenerate spiece.model from the same base model
        from transformers import AutoTokenizer
        AutoTokenizer.from_pretrained(args.model).save_pretrained(args.best)
    shutil.copy(spiece, out / "spiece.model")
    size = sum(p.stat().st_size for p in out.rglob("*")) / 1e6
    shutil.make_archive(str(out), "zip", out)
    print(f"exported {out} ({size:.1f} MB) and {out}.zip")


if __name__ == "__main__":
    main()
