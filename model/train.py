# encoding=utf-8
# created @2024/5/17
# created by zhanzq
#
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np


# Define IRCNN model
class IRCNN(nn.Module):
    def __init__(self, vocab_size, embedding_size, num_filters, kernel_sizes, hidden_act='gelu',
                 hidden_dropout_prob=0.2, initializer_range=0.02):
        super(IRCNN, self).__init__()

        self.embedding = nn.Embedding(vocab_size, embedding_size)

        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=embedding_size, out_channels=num_filters, kernel_size=ks)
            for ks in kernel_sizes
        ])

        self.fc = nn.Linear(num_filters * len(kernel_sizes), 1)

        # Hidden layers
        self.hidden_act = nn.GELU() if hidden_act == 'gelu' else nn.ReLU()
        self.hidden_dropout = nn.Dropout(hidden_dropout_prob)

        # Initialize weights
        self.apply(self._init_weights)

    def forward(self, input_ids):
        # Embedding layer
        embedded = self.embedding(input_ids)  # [batch_size, seq_length, embedding_size]
        embedded = embedded.permute(0, 2, 1)  # [batch_size, embedding_size, seq_length]

        # Convolutional layers
        conv_outputs = [conv(embedded) for conv in self.convs]  # [batch_size, num_filters, seq_length - ks + 1]

        # Max pooling over time
        pooled_outputs = [torch.max(conv, dim=2)[0] for conv in conv_outputs]  # [batch_size, num_filters]

        # Concatenate features
        cat_output = torch.cat(pooled_outputs, dim=1)  # [batch_size, num_filters * len(kernel_sizes)]

        # Fully connected layer
        logits = self.fc(cat_output)  # [batch_size, 1]

        return logits

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Conv1d)):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if module.bias is not None:
                module.bias.data.zero_()


# Function to train the model
def train_model(model, train_loader, optimizer, criterion, num_epochs=5):
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print('Epoch %d, Loss: %.4f' % (epoch + 1, total_loss))


# Function to save the model
def save_model(model, filepath):
    torch.save(model.state_dict(), filepath)
    print("Model saved to:", filepath)


# Function to load the model
def load_model(model, filepath):
    model.load_state_dict(torch.load(filepath))
    model.eval()
    print("Model loaded from:", filepath)


# Function for model inference
def predict(model, input_ids):
    model.eval()
    with torch.no_grad():
        outputs = model(input_ids)
        predictions = torch.sigmoid(outputs)
    return predictions


# Example usage
if __name__ == '__main__':
    # Example data
    vocab_size = 21128
    embedding_size = 128
    num_filters = 128
    kernel_sizes = [2, 3, 4, 5]
    hidden_act = 'gelu'
    hidden_dropout_prob = 0.2
    initializer_range = 0.02
    num_epochs = 5
    learning_rate = 0.001
    batch_size = 32

    # Create model
    model = IRCNN(vocab_size, embedding_size, num_filters, kernel_sizes, hidden_act, hidden_dropout_prob)

    # Example data tensors (replace with your actual data)
    train_inputs = torch.randint(0, vocab_size, (1000, 50))  # Example input tensor
    train_labels = torch.randint(0, 2, (1000, 1)).float()  # Example label tensor

    # Create DataLoader
    train_data = TensorDataset(train_inputs, train_labels)
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)

    # Define loss function and optimizer
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Train the model
    train_model(model, train_loader, optimizer, criterion, num_epochs=num_epochs)

    # Save the model
    save_model(model, "ircnn_model.pth")

    # Load the model
    loaded_model = IRCNN(vocab_size, embedding_size, num_filters, kernel_sizes, hidden_act, hidden_dropout_prob)
    load_model(loaded_model, "ircnn_model.pth")

    # Example inference
    example_input = torch.randint(0, vocab_size, (1, 50))  # Example input for inference
    predictions = predict(loaded_model, example_input)
    print("Predictions:", predictions.item())
