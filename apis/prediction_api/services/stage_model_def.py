import torch
import torch.nn as nn


class StageSegmentationLSTM(nn.Module):
    """BiLSTM-based stage segmentation model matching the training checkpoints.

    Architecture (per training notebooks):
    - BiLSTM encoder over pose features (T, 132)
    - LayerNorm over hidden dimension
    - Linear classifier to per-frame logits (T, num_classes)
    """

    def __init__(
        self,
        input_size: int = 132,
        hidden_size: int = 128,
        num_layers: int = 3,
        num_classes: int = 5,
        bidirectional: bool = True,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_classes = num_classes
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=bidirectional,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # LayerNorm matches the "norm.weight" / "norm.bias" entries in checkpoints
        self.norm = nn.LayerNorm(hidden_size * self.num_directions)

        # Classifier head, matches "classifier.*" in checkpoints
        self.classifier = nn.Linear(hidden_size * self.num_directions, num_classes)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: (batch, T, input_size)
            lengths: (batch,) sequence lengths

        Returns:
            (batch, T, num_classes) per-frame logits.
        """

        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths.cpu(), batch_first=True, enforce_sorted=True
        )

        packed_out, _ = self.lstm(packed)

        out, _ = nn.utils.rnn.pad_packed_sequence(packed_out, batch_first=True)

        out = self.norm(out)
        logits = self.classifier(out)
        return logits