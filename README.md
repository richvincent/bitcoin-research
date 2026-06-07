# bitcoin-research

A small proof-of-concept exploring read and write access to the Bitcoin blockchain in Python. Built as a functionality test for reading address data from a public API and writing/retrieving arbitrary data on the Bitcoin testnet.

## Overview

This repo contains two independent experiments:

- **read_from_blockchain.py** — Queries the public blockchain.info API to retrieve JSON transaction data for a list of Bitcoin addresses.
- **write_to_blockchain.py** — Demonstrates storing and retrieving arbitrary data on the Bitcoin testnet as a nulldata (OP_RETURN) output, plus signing and verifying a message with a key, using the btctxstore and blockchain libraries.

## Requirements

- Python 2.x
- Dependencies listed in requirements.txt

    pip install -r requirements.txt

## Usage

Read address data from the blockchain:

    python read_from_blockchain.py

Run the testnet write/retrieve demo:

    python write_to_blockchain.py

> **Note:** The write demo runs against the Bitcoin testnet only. Any keys included in the source are throwaway test keys, never commit real private keys or mainnet wallet credentials.

## Status

Experimental / educational. This is an early research spike rather than a production tool.
