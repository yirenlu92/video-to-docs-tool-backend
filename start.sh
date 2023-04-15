#!/bin/bash

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Set up the Rust environment
source $HOME/.cargo/env

# Install Python dependencies
pip install -r requirements.txt
