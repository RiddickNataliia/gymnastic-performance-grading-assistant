import torch
import torch.nn as nn

class GymnasticsLSTM(nn.Module):
    def __init__(self, input_size=132, hidden_size=64, num_layers=4, bidirectional=True):
        super(GymnasticsLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1

        # LSTM to encode sequence
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.3,
            bidirectional=bidirectional
        )

        # Fully connected head for stage grade
        self.fc = nn.Sequential(
            nn.Linear(hidden_size * self.num_directions, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1)  # single output for pass/fail probability
        )

    def forward(self, x, lengths):
        """
        x: (batch, T, input_size)
        lengths: (batch,)
        returns: (batch, 1) logits for grading
        """
        # Pack padded sequence
        packed = nn.utils.rnn.pack_padded_sequence(x, lengths.cpu(), batch_first=True, enforce_sorted=True)
        _, (hn, _) = self.lstm(packed)  # hn: (num_layers * num_directions, batch, hidden_size)

        # Reshape to (num_layers, num_directions, batch, hidden_size)
        batch = hn.size(1)
        hn = hn.view(self.num_layers, self.num_directions, batch, self.hidden_size)

        # Take last layer's hidden states for all directions
        last_layer = hn[-1]  # (num_directions, batch, hidden_size)

        # Concatenate directions
        last_hidden = last_layer.permute(1, 0, 2).contiguous().view(batch, -1)  # (batch, hidden_size*num_directions)

        # Pass through FC head
        out = self.fc(last_hidden)  # (batch, 1)
        return out
