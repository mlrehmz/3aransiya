# Technical documentation

The root [README](../README.md) is the product overview and quick-start guide. These notes document the data pipeline, model experiments, runtime checks, and release evaluation.

## Suggested reading order

1. [Release evaluation and reproduction](31-release.md): final model composition, held-out word results, and end-to-end build commands.
2. [Contextual extension evaluation](33-contextual-extension.md): sentence checks, foreign-language copying, and practical limits.
3. [Corpus expansion audit](22-corpus-expansion-audit.md): how the training pool was screened and kept separate from validation and test.
4. [Routing and speed results](28-fedora-training-and-routing-results.md): model selection, lookup thresholds, unseen-word results, and CPU latency.
5. [Sentence Transformer pilot](32-sentence-transformer-pilot.md): an alternative architecture that was tested and not selected.

## Engineering record

The numbered notes preserve the implementation and evaluation trail. They are grouped below by topic; earlier design notes are useful for methodology, while the release guides above describe the final state.

### Data and evaluation

- [DODa data exploration](01-doda-data-exploration.md)
- [Leakage-aware sentence split](02-doda-sentence-split.md)
- [Word alignment pilot](03-training-alignment-pilot.md)
- [Training reference audit](04-common-word-reference-audit.md)
- [Scoring rubric](05-common-word-scoring-rubric.md)
- [Validation benchmark](06-validation-benchmark.md)
- [Validation disagreement review](17-validation-disagreement-audit.md)
- [Grounded corpus audit](22-corpus-expansion-audit.md)
- [Grounded data enrichment audit](29-grounded-enrichment-audit.md)

### Models and training

- [Shared model pilot design](07-shared-model-pilot-design.md)
- [GRU encoder–decoder](11-gru-encoder-decoder.md) · [GRU/CTC](12-gru-ctc.md)
- [Resumable Colab workflow](15-colab-t4-training.md) · [initial results](16-colab-pilot-results.md) · [six-epoch comparison](18-six-epoch-colab-comparison.md)
- [Accuracy, generalization, and speed research](23-model-accuracy-generalization-speed.md)
- [Targeted spelling checks](19-short-arabizi-error-check.md) · [reviewed correction set](20-darija-correction-set-draft.md) · [fine-tuning plan](21-darija-fine-tuning-plan.md)
- [Colab v2 workflow](24-colab-v2-workflow.md) · [v2 results](25-v2-results-and-human-weighting.md)
- [CPU training pilot](27-fedora-cpu-training-pilot.md) · [route evaluation](28-fedora-training-and-routing-results.md)
- [Spelling enrichment](30-spelling-enrichment-fine-tuning.md)
- [Sentence Transformer experiment](32-sentence-transformer-pilot.md)

### Runtime and app integration

- [Fedora CPU environment](08-fedora-cpu-runtime.md) · [Kaggle GPU preflight](09-kaggle-gpu-runtime.md)
- [Shared model data loader](10-shared-model-data.md)
- [Headless predictor adapter](13-headless-predictor-adapter.md) · [inference bundle format](14-inference-bundle-spec.md)
- [Sentence error audit](26-scratchpad-sentence-error-audit.md)
- [Scratchpad integration and contextual behavior](33-contextual-extension.md)
