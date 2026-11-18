"""Character GRU encoder–decoder with teacher forcing and bounded decoding."""

import torch
from torch import nn
from torch.nn import functional as F
from torch.nn.utils.rnn import pack_padded_sequence

from model_pilot.data import MAX_TARGET_LENGTH, PAD


class EncoderDecoder(nn.Module):
    def __init__(self, vocabulary):
        super().__init__()
        self.target_chars = vocabulary.target_chars
        self.bos = len(self.target_chars) + 1
        self.eos = self.bos + 1
        target_size = self.eos + 1
        self.input_embedding = nn.Embedding(len(vocabulary.input_chars) + 2, 32, padding_idx=PAD)
        self.encoder = nn.GRU(32, 64, batch_first=True, bidirectional=True)
        self.target_embedding = nn.Embedding(target_size, 32, padding_idx=PAD)
        self.decoder = nn.GRU(32, 128, batch_first=True)
        self.output = nn.Linear(128, target_size)

    def _encode(self, inputs, input_lengths):
        packed = pack_padded_sequence(
            self.input_embedding(inputs), input_lengths, batch_first=True, enforce_sorted=False
        )
        _, terminal = self.encoder(packed)
        return torch.cat((terminal[0], terminal[1]), dim=-1).unsqueeze(0)

    def forward(self, batch):
        """Return teacher-forced logits for target characters and the end marker."""
        begin = batch.targets.new_full((batch.targets.size(0), 1), self.bos)
        decoder_inputs = torch.cat((begin, batch.targets), dim=1)
        hidden = self._encode(batch.inputs, batch.input_lengths)
        states, _ = self.decoder(self.target_embedding(decoder_inputs), hidden)
        return self.output(states)

    def loss(self, batch):
        logits = self(batch)
        labels = F.pad(batch.targets, (0, 1), value=PAD)
        end_positions = batch.target_lengths.to(labels.device).unsqueeze(1)
        labels.scatter_(1, end_positions, self.eos)
        return F.cross_entropy(logits.transpose(1, 2), labels, ignore_index=PAD)

    @torch.inference_mode()
    def greedy(self, inputs, input_lengths):
        """Return Arabic strings, or None for empty or overlength predictions."""
        hidden = self._encode(inputs, input_lengths)
        token = inputs.new_full((inputs.size(0), 1), self.bos)
        strings = [[] for _ in range(inputs.size(0))]
        finished = [False] * inputs.size(0)
        for step in range(MAX_TARGET_LENGTH + 1):
            states, hidden = self.decoder(self.target_embedding(token), hidden)
            logits = self.output(states)
            logits[..., PAD] = -torch.inf
            logits[..., self.bos] = -torch.inf
            token = logits.argmax(dim=-1)
            for row, choice in enumerate(token.squeeze(1).tolist()):
                if finished[row]:
                    continue
                if choice == self.eos:
                    finished[row] = True
                elif step < MAX_TARGET_LENGTH:
                    strings[row].append(self.target_chars[choice - 1])
            if all(finished):
                break
        return ["".join(chars) if done and chars else None for chars, done in zip(strings, finished)]
