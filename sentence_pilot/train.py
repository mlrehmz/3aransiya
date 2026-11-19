"""Train or resume a CPU sentence Transformer on the frozen DODa development split."""

import argparse
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import platform
from time import monotonic

import torch

from model_pilot.train import atomic_write
from .data import Alphabet, batches, encode_batch, read_pairs
from .model import SentenceTransformer


def save(path, model, optimizer, step, settings):
    stream = BytesIO()
    torch.save({
        "settings": settings, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
        "step": step, "rng": torch.get_rng_state(),
    }, stream)
    atomic_write(path, stream.getvalue())


def load_model(path):
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    model = SentenceTransformer(Alphabet(checkpoint["settings"]["alphabet"]))
    model.load_state_dict(checkpoint["model"])
    return model.eval(), checkpoint["step"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("sentences", "assignment", "output"):
        parser.add_argument(argument, type=Path)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--steps", type=int, help="stop after this many additional batches")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--mixed", action="store_true", help="add synthetic English copy spans")
    args = parser.parse_args()
    if min(args.epochs, args.threads, args.steps if args.steps is not None else 1) < 1:
        parser.error("epochs, threads, and steps must be positive")

    torch.set_num_threads(args.threads)
    torch.manual_seed(42)
    rows = read_pairs(args.sentences, args.assignment, mixed=args.mixed)["train"]
    alphabet = Alphabet.from_pairs(rows)
    batch_size = 64
    settings = {
        "alphabet": list(alphabet.chars), "rows": len(rows), "mixed": args.mixed,
        "batch_size": batch_size, "threads": args.threads, "torch": str(torch.__version__),
        "python": platform.python_version(),
        "revision": sha256(b"".join(
            path.read_bytes() for path in sorted(Path(__file__).parent.glob("*.py"))
            if path.name != "evaluate.py"
        )).hexdigest(),
    }
    model = SentenceTransformer(alphabet)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / "checkpoint.pt"
    step = 0
    if path.is_file():
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        if checkpoint["settings"] != settings:
            parser.error("checkpoint settings differ; use a separate output directory")
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        step = checkpoint["step"]
        torch.set_rng_state(checkpoint["rng"])

    batches_per_epoch = (len(rows) + batch_size - 1) // batch_size
    target = args.epochs * batches_per_epoch
    end = min(target, step + args.steps) if args.steps is not None else target
    print(f"Training on {len(rows):,} sentences, {batches_per_epoch} batches per epoch, "
          f"{sum(p.numel() for p in model.parameters()):,} parameters. Starting at {step}/{end}.", flush=True)
    started = monotonic()
    while step < end:
        epoch, offset = divmod(step, batches_per_epoch)
        order = batches(rows, batch_size, 42 + epoch)
        model.train()
        for indices in order[offset:offset + end - step]:
            source, target_tokens = encode_batch([rows[index] for index in indices], alphabet)
            optimizer.zero_grad(set_to_none=True)
            loss = model.loss(source, target_tokens)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            optimizer.step()
            step += 1
            new_epoch = step % batches_per_epoch == 0
            if new_epoch or step % 100 == 0 or step == end:
                save(path, model, optimizer, step, settings)
                print(f"Step {step}/{end}, loss {loss:.4f}, elapsed {monotonic() - started:.1f}s", flush=True)
            if new_epoch:
                epoch_path = args.output / f"epoch-{epoch + 1}.pt"
                atomic_write(epoch_path, path.read_bytes())


if __name__ == "__main__":
    main()
