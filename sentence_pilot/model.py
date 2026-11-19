"""A small encoder–decoder Transformer over characters."""

import torch
from torch import nn
from torch.nn import functional as F

from .data import END, MAX_CHARS, PAD, START, UNKNOWN


class SentenceTransformer(nn.Module):
    def __init__(self, alphabet):
        super().__init__()
        self.alphabet = alphabet
        size = len(alphabet.chars) + 4
        width = 64
        self.tokens = nn.Embedding(size, width, padding_idx=PAD)
        self.positions = nn.Embedding(MAX_CHARS + 2, width)
        self.network = nn.Transformer(
            d_model=width, nhead=4, num_encoder_layers=2, num_decoder_layers=2,
            dim_feedforward=128, dropout=0.1, batch_first=True,
        )
        self.output = nn.Linear(width, size)
        self.output.weight = self.tokens.weight
        nn.init.normal_(self.tokens.weight, std=width ** -0.5)
        with torch.no_grad():
            self.tokens.weight[PAD].zero_()

    def embed(self, ids):
        return self.tokens(ids) * 8 + self.positions(torch.arange(ids.size(1), device=ids.device))

    def encode(self, source):
        return self.network.encoder(self.embed(source), src_key_padding_mask=source.eq(PAD))

    def decode(self, target, memory, source_mask):
        causal = torch.ones((target.size(1), target.size(1)), dtype=torch.bool, device=target.device).triu(1)
        return self.output(self.network.decoder(
            self.embed(target), memory, tgt_mask=causal, tgt_is_causal=True,
            memory_key_padding_mask=source_mask,
        ))

    def loss(self, source, target):
        start = target.new_full((len(target), 1), START)
        prior = torch.cat((start, target[:, :-1]), dim=1)
        logits = self.decode(prior, self.encode(source), source.eq(PAD))
        return F.cross_entropy(logits.transpose(1, 2), target, ignore_index=PAD)

    @torch.inference_mode()
    def predict(self, inputs):
        source = nn.utils.rnn.pad_sequence(
            [self.alphabet.encode(text) for text in inputs], batch_first=True,
        )
        memory = self.encode(source)
        mask = source.eq(PAD)
        prior = source.new_full((len(source), 1), START)
        finished = torch.zeros(len(source), dtype=torch.bool)
        limits = torch.tensor([min(MAX_CHARS, 2 * len(text) + 8) for text in inputs])
        for step in range(1, MAX_CHARS + 2):
            scores = self.decode(prior, memory, mask)[:, -1, :]
            scores[:, [PAD, START, UNKNOWN]] = -torch.inf
            token = scores.argmax(-1)
            token[finished] = END
            prior = torch.cat((prior, token.unsqueeze(1)), dim=1)
            finished |= token.eq(END) | (limits <= step)
            if finished.all():
                break
        outputs = []
        for tokens in prior[:, 1:].tolist():
            stop = tokens.index(END) if END in tokens else len(tokens)
            outputs.append(self.alphabet.decode(tokens[:stop]))
        return outputs
