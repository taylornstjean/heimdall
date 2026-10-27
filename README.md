# Heimdall

Heimdall is a locally hosted web application designed to provide real time updates to the Minor Planet Center (MPC) Near-Earth Object Confirmation Page (NEOCP).

This project is in the early stages of development and currently only provides very basic functionality.

If you find this useful and would like to contribute, please feel free to make a PR!

## Install and Run

```bash
pip install heimdall-neo
heimdall
```

This starts the server at http://127.0.0.1:8765 and opens it in your browser.

| Option         | Description                                 |
| -------------- | --------------------------------------------- |
| `--port 9000`  | Use a different port                          |
| `--host`       | Interface to bind (default `127.0.0.1`)       |
| `--no-browser` | Don't open a browser window                   |
