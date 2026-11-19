"""Fine-tune a sentence checkpoint on mixed-script copy examples with Darija replay."""

import argparse
from hashlib import sha256
from pathlib import Path
import random

import torch

from sentence_pilot.data import MAX_CHARS, encode_batch, read_pairs
from sentence_pilot.train import load_model, save


FRENCH_SPANS = (
    "je comprends très bien", "tu peux attendre un peu", "merci pour ton aide",
    "on se voit vendredi", "j'ai reçu ton message", "c'est une bonne idée",
    "le train part bientôt", "le rendez-vous est confirmé", "pas de problème",
    "ça ne me dérange pas", "envoie-moi le document", "je termine mon travail",
    "tu as mon numéro", "je pars dans cinq minutes", "c'était vraiment sympa",
)


def mixed_examples(rows, originals, alphabet, rng):
    result = []
    human_pairs = set(originals)
    for source, target in rows[len(originals):]:
        # The training-only English span appears unchanged on both sides of the separator.
        foreign, _, darija = source.partition(" / ")
        copied, _, arabic = target.partition(" / ")
        at_start = foreign == copied and (darija, arabic) in human_pairs
        if not at_start:
            darija, _, foreign = source.rpartition(" / ")
            arabic, _, copied = target.rpartition(" / ")
            if foreign != copied or (darija, arabic) not in human_pairs:
                raise ValueError("synthetic pair has no verified copied span")
        if rng.randrange(4) == 0:
            foreign = rng.choice(FRENCH_SPANS)
        if any(char not in alphabet.ids for char in foreign):
            continue
        separator = rng.choice((", ", ". ", "! ", " "))
        if at_start:
            pair = foreign + separator + darija, foreign + separator + arabic
        else:
            pair = darija + separator + foreign, arabic + separator + foreign
        if max(map(len, pair)) <= MAX_CHARS:
            result.append(pair)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("sentences", "assignment", "checkpoint", "output"):
        parser.add_argument(argument, type=Path)
    parser.add_argument("--steps", type=int, default=300)
    args = parser.parse_args()
    if args.steps < 1 or args.output.exists():
        parser.error("steps must be positive and the output must be new")
    torch.set_num_threads(4)
    torch.manual_seed(43)
    rng = random.Random(43)
    originals = read_pairs(args.sentences, args.assignment)["train"]
    training = read_pairs(args.sentences, args.assignment, mixed=True)["train"]
    model, base_step = load_model(args.checkpoint)
    mixed = mixed_examples(training, originals, model.alphabet, rng)
    base_digest = sha256(args.checkpoint.read_bytes()).hexdigest()
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0003)
    args.output.mkdir(parents=True, exist_ok=False)
    print(f"Adapting on {len(mixed):,} mixed examples and {len(originals):,} human sentences", flush=True)
    for step in range(1, args.steps + 1):
        pairs = rng.sample(originals, 48) + rng.sample(mixed, 16)
        source, target = encode_batch(pairs, model.alphabet)
        optimizer.zero_grad(set_to_none=True)
        loss = model.loss(source, target)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
        if step % 100 == 0 or step == args.steps:
            save(args.output / "checkpoint.pt", model, optimizer, step, {
                "alphabet": list(model.alphabet.chars), "base_step": base_step,
                "base_sha256": base_digest,
            })
            print(f"Copy adaptation step {step}/{args.steps}, loss {loss:.4f}", flush=True)


if __name__ == "__main__":
    main()
