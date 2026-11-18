"""Bidirectional character GRU with an expanded CTC output head."""

from itertools import groupby

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from model_pilot.data import CTC_EXPANSION, MAX_TARGET_LENGTH, PAD

BLANK = 0


class GruCtc(nn.Module):
    def __init__(self, vocabulary):
        super().__init__()
        self.target_chars = vocabulary.target_chars
        self.classes = len(self.target_chars) + 1
        self.input_embedding = nn.Embedding(len(vocabulary.input_chars) + 2, 32, padding_idx=PAD)
        self.encoder = nn.GRU(32, 64, batch_first=True, bidirectional=True)
        self.output = nn.Linear(128, CTC_EXPANSION * self.classes)
        self.ctc_loss = nn.CTCLoss(blank=BLANK)

    def forward(self, inputs, input_lengths):
        """Return batch-first frame logits and each word's valid frame count."""
        packed = pack_padded_sequence(
            self.input_embedding(inputs), input_lengths, batch_first=True, enforce_sorted=False
        )
        encoded, _ = self.encoder(packed)
        states, _ = pad_packed_sequence(encoded, batch_first=True)
        logits = self.output(states).reshape(inputs.size(0), -1, self.classes)
        return logits, input_lengths * CTC_EXPANSION

    def loss(self, batch):
        logits, frame_lengths = self(batch.inputs, batch.input_lengths)
        log_probs = logits.log_softmax(dim=-1).transpose(0, 1).contiguous()
        return self.ctc_loss(log_probs, batch.targets, frame_lengths, batch.target_lengths)

    @torch.inference_mode()
    def greedy(self, inputs, input_lengths):
        """Return Arabic strings, or None for empty or overlength predictions."""
        logits, frame_lengths = self(inputs, input_lengths)
        best_paths = logits.argmax(dim=-1).tolist()
        outputs = []
        for path, length in zip(best_paths, frame_lengths.tolist()):
            chars = [
                self.target_chars[token - 1]
                for token, _ in groupby(path[:length])
                if token != BLANK
            ]
            outputs.append("".join(chars) if 1 <= len(chars) <= MAX_TARGET_LENGTH else None)
        return outputs
