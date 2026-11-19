# Expanded v2 Colab workflow

The [v2 notebook](../notebooks/colab_t4_v2.ipynb) runs one full pass per candidate on a T4 with the existing FP32 AdamW setup and per-step checkpoints. It is separate from the v1 notebook. It reads `/content/doda-word-pairs-v2.json` and writes to `/content/outputs/t4-v2-one-pass/`.

Both candidates train on the same **1,170,570 occurrences**. Two grounded rows were excluded at load time after checking their source sentences. Record 265842 token 7 and record 419166 token 13 each paired the standalone Latin preposition `l` with the Arabic preposition plus its noun. The stored v2 dataset remains intact. The exclusions also bring every training target within the existing CTC frame budget.

The validated model vocabulary has 85 input and 60 output characters. All 20,081 v1 validation occurrences are retained. The benchmark uses the original human training forms to identify the v1 top 500 and the original unseen slice. It reports the original 3,389 unseen occurrences both together and as 677 now seen in v2 and 2,712 still unseen. The locked test remains excluded.

## Official CLI

Google Colab CLI **0.8.0** was installed in the local ignored data directory using uv. Its T4, notebook execution, upload, and download commands are documented by Google. Authentication uses a local OAuth flow; account credentials remain outside the repository. [Official Colab CLI documentation](https://github.com/googlecolab/google-colab-cli)

From the repository root, run `./data/colab-bin/colab usage` to complete authorization and check available compute. Once authenticated, the CLI can create a named T4 session, upload the verified dataset to `/content`, run the notebook, and download checkpoints, reports, and bundles before stopping the session. Use a named session so a failed execution can be investigated or resumed without discarding its local files.

The loader, validation counts, notebook settings, and embedded source were verified locally. No remote runtime was provisioned and no dataset was uploaded during setup.

## Training output in Colab

The training cell forwards the child process's stdout and stderr into notebook output and prints the run directory before starting each candidate. This changes log display only. The embedded trainer and checkpoint identity remain the same. A local notebook-cell fixture reproduced the missing output and verified live forwarding after the fix.
