"""Fine-tune t5-small on ASLG-PC12 (English -> ASL gloss). Kaggle / Colab only (ADR 0005).

Run on a Kaggle GPU notebook (P100 or T4):
    !pip install -q -r requirements-train.txt        # or paste the pins below
    !python train_t5_gloss.py --epochs 3 --out /kaggle/working/t5_gloss
Then export with export_ct2.py. Nothing here is imported by the deployed app.

Data: achrafothman/aslg_pc12 (87,710 pairs, CC BY-NC 4.0). Only a `train` split exists, so a fixed-seed
90/5/5 split is made here and the split indices are saved with the results so the evaluation is reproducible.
Known limitation stated up front: the glosses were rule-generated from parliamentary text, so test-split
scores say little about news; the honest comparison against the rule pass is on the curated items.
"""
import argparse
import json
import random
import time
from pathlib import Path

try:  # behind a TLS-inspecting proxy the OS trust store is the one that works; harmless elsewhere
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import evaluate
import numpy as np
import torch
from datasets import load_dataset
from transformers import (AutoTokenizer, DataCollatorForSeq2Seq, Seq2SeqTrainer, Seq2SeqTrainingArguments,
                          T5ForConditionalGeneration)

PREFIX = "translate English to ASL gloss: "
MAX_LEN = 64
SEED = 20260903


def clean(s):
    return s.replace("﻿", "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="google-t5/t5-small")
    ap.add_argument("--epochs", type=float, default=3)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--out", default="t5_gloss")
    ap.add_argument("--limit", type=int, default=0, help="debug: use only N training rows")
    args = ap.parse_args()
    random.seed(SEED)
    torch.manual_seed(SEED)

    ds = load_dataset("achrafothman/aslg_pc12")["train"]
    ds = ds.map(lambda r: {"text": clean(r["text"]), "gloss": clean(r["gloss"])})
    ds = ds.filter(lambda r: r["text"] and r["gloss"])
    idx = list(range(len(ds)))
    random.shuffle(idx)
    n_test = n_val = len(idx) // 20
    split = {"test": idx[:n_test], "val": idx[n_test : n_test + n_val], "train": idx[n_test + n_val :]}
    if args.limit:
        split["train"] = split["train"][: args.limit]
    parts = {k: ds.select(v) for k, v in split.items()}
    print({k: len(v) for k, v in parts.items()})

    tok = AutoTokenizer.from_pretrained(args.model)
    model = T5ForConditionalGeneration.from_pretrained(args.model)

    def encode(batch):
        x = tok([PREFIX + t for t in batch["text"]], max_length=MAX_LEN, truncation=True)
        y = tok(text_target=batch["gloss"], max_length=MAX_LEN, truncation=True)
        x["labels"] = y["input_ids"]
        return x

    enc = {k: v.map(encode, batched=True, remove_columns=v.column_names) for k, v in parts.items()}
    bleu, chrf = evaluate.load("sacrebleu"), evaluate.load("chrf")

    def metrics(p):
        preds, labels = p
        preds = np.where(preds != -100, preds, tok.pad_token_id)
        labels = np.where(labels != -100, labels, tok.pad_token_id)
        ps = [s.strip() for s in tok.batch_decode(preds, skip_special_tokens=True)]
        ls = [[s.strip()] for s in tok.batch_decode(labels, skip_special_tokens=True)]
        return {"bleu": bleu.compute(predictions=ps, references=ls)["score"], "chrf": chrf.compute(predictions=ps, references=ls)["score"]}

    out = Path(args.out)
    targs = Seq2SeqTrainingArguments(
        output_dir=str(out / "ckpt"), learning_rate=args.lr, per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch * 2, num_train_epochs=args.epochs, weight_decay=0.01,
        eval_strategy="epoch", save_strategy="epoch", save_total_limit=1, load_best_model_at_end=True,
        metric_for_best_model="chrf", predict_with_generate=True, generation_max_length=MAX_LEN,
        fp16=torch.cuda.is_available(), logging_steps=200, report_to=[], seed=SEED,
    )
    trainer = Seq2SeqTrainer(model=model, args=targs, train_dataset=enc["train"], eval_dataset=enc["val"],
                             data_collator=DataCollatorForSeq2Seq(tok, model=model), processing_class=tok, compute_metrics=metrics)
    t = time.time()
    trainer.train()
    train_s = time.time() - t

    test = trainer.predict(enc["test"], max_length=MAX_LEN)
    samples = []
    for i in range(10):
        r = parts["test"][i]
        pred = tok.decode(np.where(test.predictions[i] != -100, test.predictions[i], tok.pad_token_id), skip_special_tokens=True)
        samples.append({"text": r["text"], "gloss": r["gloss"], "pred": pred.strip()})
    best = out / "best"
    trainer.save_model(str(best))
    tok.save_pretrained(str(best))
    results = {"model": args.model, "epochs": args.epochs, "lr": args.lr, "batch": args.batch, "train_rows": len(parts["train"]),
               "train_seconds": round(train_s), "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
               "test": {k.replace("test_", ""): v for k, v in test.metrics.items() if k in ("test_bleu", "test_chrf")},
               "samples": samples, "split_seed": SEED, "split_sizes": {k: len(v) for k, v in parts.items()}}
    (out / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    (out / "split_test_indices.json").write_text(json.dumps(split["test"]), encoding="utf-8")
    print(json.dumps(results, indent=1)[:2000])


if __name__ == "__main__":
    main()
