# Fedora CPU training pilot

The 25% human-data encoder–decoder can run locally with the same pinned v2 dataset, batch schedule, FP32 AdamW settings, and validation as the Colab experiment. The trainer accepts `--device cpu` and keeps T4 as its default. The local run uses PyTorch 2.11.0+cpu on an Intel Core i5-8250U.

Three runs processed 48 real batches each, using the same initial weights and batch order. The table reports median wall time after discarding warm-up, with a checkpoint written after every update.

| CPU threads | Time per update including save | Time spent saving |
| --- | ---: | ---: |
| 1 | 58.3 ms | 17.0 ms |
| 2 | 55.6 ms | 17.2 ms |
| 4 | 56.5 ms | 19.6 ms |

The two-thread result projects to about 8.5 minutes for 9,146 updates. Dataset loading, final validation and export, and sustained CPU performance can change the end-to-end time. The thread timings are close. Two is the fastest setting measured, so the recommended full run would resume its checkpoint with `OMP_NUM_THREADS=2` and retain per-update saves.

The pilot stores checkpoints under `outputs/fedora-v2-human25/`. It measures speed only. The full pass and its final validation require approval before proceeding.

The CPU command resumed the two-thread run from step 48 and saved step 56. All three checkpoint recovery tests passed. A full run can resume with the command below.

```bash
OMP_NUM_THREADS=2 .venv/bin/python -m model_pilot.train \
  data/doda-word-pairs-v2.json outputs/fedora-v2-human25/threads-2 \
  --device cpu --architecture gru_encoder_decoder_v1 --dataset-version v2 \
  --human-weighted --epochs 1
```
