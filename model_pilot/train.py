"""Train or resume one pilot candidate and export its final inference bundle."""

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
from io import BytesIO
import json
import math
import os
import platform
from pathlib import Path
import random
import tempfile

import torch

from model_pilot.bundle import ARCHITECTURES, BundlePredictor, load_bundle, write_bundle
from model_pilot.data import DATASETS, collate, load_development_data
from validation_benchmark import benchmark


def atomic_write(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
            output.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


class Checkpoints:
    """Two rolling, checksummed slots on the persistent run directory."""

    def __init__(self, directory):
        self.slots = tuple(directory / f"checkpoint-{i}.bin" for i in range(2))
        self.generation = 0

    def restore(self, settings):
        found = []
        for slot in self.slots:
            try:
                content = slot.read_bytes()
            except FileNotFoundError:
                continue
            digest, _, payload = content.partition(b"\n")
            if digest != sha256(payload).hexdigest().encode("ascii"):
                print(f"Ignoring incomplete checkpoint {slot.name}", flush=True)
                found.append(None)
                continue
            state = torch.load(BytesIO(payload), map_location="cpu", weights_only=True)
            if state["settings"] != settings:
                raise ValueError("checkpoint settings differ; restore the original settings or use a new run folder")
            found.append(state)
        valid = [state for state in found if state is not None]
        if not valid:
            if found:
                raise ValueError("no valid checkpoint remains; preserve these files for recovery")
            return None
        newest = max(valid, key=lambda state: state["generation"])
        self.generation = newest["generation"]
        return newest

    def save(self, state):
        generation = self.generation + 1
        stream = BytesIO()
        torch.save({**state, "generation": generation}, stream)
        payload = stream.getvalue()
        atomic_write(self.slots[generation % 2], sha256(payload).hexdigest().encode("ascii") + b"\n" + payload)
        self.generation = generation

    def digest(self):
        return sha256(self.slots[self.generation % 2].read_bytes()).hexdigest()


@dataclass(frozen=True)
class Schedule:
    epochs: int
    batch_size: int
    seed: int
    learning_rate: float = 0.001
    human_weighted: bool = False


def sample_source(pool, count, rng):
    if not pool:
        raise ValueError("both training sources must contain occurrences")
    order = []
    while len(order) < count:
        rng.shuffle(pool)
        order.extend(pool[:count - len(order)])
    return order


def weighted_batches(rows, schedule, epoch):
    pools = defaultdict(list)
    for index, row in enumerate(rows):
        pools[row["source"]].append(index)
    sizes = [
        min(schedule.batch_size, len(rows) - offset)
        for offset in range(0, len(rows), schedule.batch_size)
    ]
    rng = random.Random(schedule.seed + epoch)
    human_count = sum(size // 4 for size in sizes)
    human = sample_source(pools["doda_human"], human_count, rng)
    grounded = sample_source(pools["doda_grounded"], len(rows) - human_count, rng)
    batches = []
    hi = gi = 0

    def by_length(index):
        return len(rows[index]["latin"])

    for offset in range(0, len(sizes), 32):
        chunk = sizes[offset:offset + 32]
        h_count = sum(size // 4 for size in chunk)
        g_count = sum(chunk) - h_count
        h_rows = iter(sorted(human[hi:hi + h_count], key=by_length))
        g_rows = iter(sorted(grounded[gi:gi + g_count], key=by_length))
        hi += h_count
        gi += g_count
        for size in chunk:
            h_size = size // 4
            batches.append(
                [next(h_rows) for _ in range(h_size)]
                + [next(g_rows) for _ in range(size - h_size)]
            )
    # Keep the partial batch last, and mix the full length buckets.
    full_batches, final_batch = batches[:-1], batches[-1]
    rng.shuffle(full_batches)
    return [*full_batches, final_batch]


def sampling_summary(rows, batches):
    exposures = Counter()
    unique = defaultdict(set)
    for batch in batches:
        for index in batch:
            source = rows[index]["source"]
            exposures[source] += 1
            unique[source].add(index)
    return {
        source: {"exposures": count, "unique_occurrences": len(unique[source])}
        for source, count in sorted(exposures.items())
    }


def epoch_batches(rows, schedule, epoch):
    if schedule.human_weighted:
        return weighted_batches(rows, schedule, epoch)
    order = list(range(len(rows)))
    rng = random.Random(schedule.seed + epoch)
    rng.shuffle(order)
    batches = []
    block = 32 * schedule.batch_size
    for offset in range(0, len(order), block):
        bucket = sorted(order[offset:offset + block], key=lambda index: len(rows[index]["latin"]))
        batches.extend(
            bucket[start:start + schedule.batch_size] for start in range(0, len(bucket), schedule.batch_size)
        )
    rng.shuffle(batches)
    return batches


def train(data, architecture, directory, schedule, device, identity, *,
          save_every=1, step_limit=None, on_epoch=None):
    settings = {
        **asdict(schedule), "architecture": architecture, "identity": identity,
        "torch": str(torch.__version__), "python": platform.python_version(),
        "device": torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu",
    }
    if not schedule.human_weighted:
        del settings["human_weighted"]
    checkpoints = Checkpoints(directory)
    saved = checkpoints.restore(settings)
    torch.manual_seed(schedule.seed)
    model = ARCHITECTURES[architecture][0](data.vocabulary).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=schedule.learning_rate)
    step = 0
    loss_sum = 0.0
    loss_count = 0
    if saved is not None:
        model.load_state_dict(saved["model"])
        optimizer.load_state_dict(saved["optimizer"])
        torch.set_rng_state(saved["cpu_rng"])
        if device.type == "cuda":
            torch.cuda.set_rng_state(saved["cuda_rng"], device)
        step, loss_sum, loss_count = saved["step"], saved["loss_sum"], saved["loss_count"]
        print(f"Resumed after {step} saved batches", flush=True)

    steps_in_epoch = (len(data.training) + schedule.batch_size - 1) // schedule.batch_size
    total_steps = steps_in_epoch * schedule.epochs
    final_step = total_steps if step_limit is None else min(total_steps, step + step_limit)
    if on_epoch is not None and step and step % steps_in_epoch == 0:
        on_epoch(step // steps_in_epoch, model, checkpoints.digest())
    while step < final_step:
        model.train()
        epoch, first_batch = divmod(step, steps_in_epoch)
        batches = epoch_batches(data.training, schedule, epoch)
        remaining = min(len(batches) - first_batch, final_step - step)
        for index in range(first_batch, first_batch + remaining):
            batch = collate([data.training[row] for row in batches[index]], data.vocabulary)
            batch = replace(batch, inputs=batch.inputs.to(device), targets=batch.targets.to(device))
            optimizer.zero_grad(set_to_none=True)
            loss = model.loss(batch)
            value = loss.item()
            if not math.isfinite(value):
                raise ValueError(f"nonfinite loss at batch {step + 1}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            optimizer.step()
            step += 1
            loss_sum += value
            loss_count += 1
            epoch_finished = step % steps_in_epoch == 0
            if epoch_finished or step == final_step or step % save_every == 0:
                checkpoints.save({
                    "settings": settings, "step": step,
                    "loss_sum": 0.0 if epoch_finished else loss_sum,
                    "loss_count": 0 if epoch_finished else loss_count,
                    "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                    "cpu_rng": torch.get_rng_state(),
                    "cuda_rng": torch.cuda.get_rng_state(device) if device.type == "cuda" else None,
                })
            if epoch_finished:
                print(f"Epoch {epoch + 1}/{schedule.epochs} mean batch loss {loss_sum / loss_count:.5f}", flush=True)
                loss_sum, loss_count = 0.0, 0
                if on_epoch is not None:
                    on_epoch(epoch + 1, model, checkpoints.digest())
            elif step % 100 == 0:
                print(f"Batch {step}/{total_steps}, loss {value:.5f}", flush=True)
    return model, checkpoints, step, total_steps


def validate(model, data, pairs, path, checkpoint_digest, device, batch_size, *, preserve_v1_slices=False):
    if path.exists():
        try:
            report = json.loads(path.read_text())
            if report["checkpoint_sha256"] == checkpoint_digest:
                return report["scores"]
        except (ValueError, KeyError, TypeError):
            pass
    model.eval()
    predictions = {}
    forms = data.validation_forms
    for offset in range(0, len(forms), batch_size):
        chunk = forms[offset:offset + batch_size]
        encoded = [torch.tensor(data.vocabulary.encode_input(word)) for word in chunk]
        inputs = torch.nn.utils.rnn.pad_sequence(encoded, batch_first=True)
        lengths = torch.tensor([len(ids) for ids in encoded])
        outputs = model.greedy(inputs.to(device), lengths)
        predictions.update((word, output) for word, output in zip(chunk, outputs) if output is not None)
    scores = benchmark(pairs, predictions, preserve_v1_slices=preserve_v1_slices)
    atomic_write(path, (json.dumps({"checkpoint_sha256": checkpoint_digest, "scores": scores}, indent=2) + "\n").encode())
    return scores


def source_digest():
    root = Path(__file__).resolve().parents[1]
    digest = sha256((root / "validation_benchmark.py").read_bytes())
    for path in sorted((root / "model_pilot").glob("*.py")):
        digest.update(path.name.encode("ascii") + b"\0" + sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("word_pairs", type=Path)
    parser.add_argument("run", type=Path)
    parser.add_argument("--architecture", choices=ARCHITECTURES, required=True)
    parser.add_argument("--dataset-version", choices=DATASETS, default="v1")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save-every", type=int, default=1)
    parser.add_argument("--steps-this-session", type=int)
    parser.add_argument("--human-weighted", action="store_true", help="use 25%% human batches for the v2 comparison")
    args = parser.parse_args()
    if min(args.epochs, args.batch_size, args.save_every) < 1 or (
        args.steps_this_session is not None and args.steps_this_session < 1
    ):
        parser.error("epochs, batch size, checkpoint interval, and session steps must be positive")
    if args.human_weighted and (
        args.dataset_version != "v2" or args.architecture != "gru_encoder_decoder_v1"
        or args.epochs != 1 or args.batch_size != 128 or args.seed != 42
    ):
        parser.error("the human-weighted comparison requires the v2 encoder–decoder, one epoch, batch size 128, and seed 42")
    if (not torch.cuda.is_available() or torch.cuda.get_device_capability(0) != (7, 5)
            or "T4" not in torch.cuda.get_device_name(0).split()):
        parser.error("a CUDA-enabled T4 is required; select the T4 runtime in Colab")
    print(f"Training on {torch.cuda.get_device_name(0)} with PyTorch {torch.__version__}", flush=True)
    artifact_sha256 = DATASETS[args.dataset_version]
    data = load_development_data(args.word_pairs, version=args.dataset_version)
    print(f"Training occurrences: {len(data.training):,}", flush=True)
    revision = source_digest()
    args.run.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda:0")
    pairs = {"train": data.training, "validation": data.validation}

    def epoch_report(epoch):
        return args.run / f"validation-epoch-{epoch:03d}.json"

    def validate_epoch(epoch, model, digest):
        scores = validate(
            model, data, pairs, epoch_report(epoch), digest, device, args.batch_size,
            preserve_v1_slices=args.dataset_version == "v2",
        )
        print(f"Validation after epoch {epoch}: {json.dumps(scores['slices'])}", flush=True)

    schedule = Schedule(args.epochs, args.batch_size, args.seed, human_weighted=args.human_weighted)
    model, checkpoints, step, total = train(
        data, args.architecture, args.run, schedule,
        device, f"{revision}:{artifact_sha256}", save_every=args.save_every,
        step_limit=args.steps_this_session, on_epoch=validate_epoch,
    )
    if step < total:
        print(f"Stopped at saved batch {step}/{total}. Rerun to resume.", flush=True)
        return
    checkpoint_digest = checkpoints.digest()
    if args.human_weighted:
        summary = sampling_summary(data.training, epoch_batches(data.training, schedule, 0))
        print(f"Completed source exposures: {json.dumps(summary)}", flush=True)
        atomic_write(args.run / "sampling.json", (
            json.dumps({"checkpoint_sha256": checkpoint_digest, "sources": summary}, indent=2) + "\n"
        ).encode())
    atomic_write(args.run / "validation.json", epoch_report(args.epochs).read_bytes())
    torch.set_num_threads(1)
    reference = BundlePredictor(model.cpu().eval(), data.vocabulary)
    destination = args.run / f"bundle-{checkpoint_digest[:16]}"
    if not destination.exists():
        digest = write_bundle(
            destination, args.architecture, data.vocabulary, model,
            source_checkpoint_sha256=checkpoint_digest, word_pairs_sha256=artifact_sha256,
            source_revision=revision,
        )
    else:
        digest = sha256((destination / "manifest.json").read_bytes()).hexdigest()
    exported = load_bundle(destination)
    successful = False
    for word in ("salam", "T7", "t7" * 9, "kanchouf", "bghit", "3lach"):
        results = []
        for predictor in (reference, exported):
            try:
                results.append(predictor.predict(word))
            except ValueError:
                results.append(None)
        if results[0] != results[1]:
            raise ValueError(f"bundle parity failed for fixed fixture {word!r}")
        successful |= results[0] is not None
    if not successful:
        raise ValueError("bundle parity fixture returned no usable predictions")
    print(f"Verified bundle: {destination}\nManifest SHA-256: {digest}", flush=True)


if __name__ == "__main__":
    main()
