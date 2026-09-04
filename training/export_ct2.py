"""Export the fine-tuned T5 to CTranslate2 int8 for the torch-free runtime (ADR 0005).

    python export_ct2.py --best /kaggle/working/t5_gloss/best --out /kaggle/working/t5_gloss_ct2

Produces: <out>/model.bin + config + spiece.model (the SentencePiece file the runtime tokenises with),
and <out>.zip for download. Attach the zip to a GitHub Release; the app fetches it on first use.
Then, locally with only ctranslate2 + sentencepiece installed, run scripts/measure_rss.py to record
the spike-3 numbers (folder size, resident memory, latency).
"""
import argparse
import shutil
from pathlib import Path

from ctranslate2.converters import TransformersConverter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--best", required=True)
    ap.add_argument("--out", default="t5_gloss_ct2")
    args = ap.parse_args()
    out = Path(args.out)
    TransformersConverter(args.best).convert(str(out), quantization="int8", force=True)
    spiece = Path(args.best) / "spiece.model"
    if not spiece.exists():  # tokenizer saved as tokenizer.json only: regenerate spiece.model from the base model
        from transformers import AutoTokenizer
        AutoTokenizer.from_pretrained("google-t5/t5-small").save_pretrained(args.best)
    shutil.copy(spiece, out / "spiece.model")
    size = sum(p.stat().st_size for p in out.rglob("*")) / 1e6
    shutil.make_archive(str(out), "zip", out)
    print(f"exported {out} ({size:.1f} MB) and {out}.zip")


if __name__ == "__main__":
    main()
