"""Entry point: `python -m capsize_social` or the `capsize-social` script."""

import logging
import os

import uvicorn


def main() -> None:
    """Run the API with uvicorn, reading host/port from the environment."""
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s"
    )
    port = int(os.environ.get("SOCIAL_PORT", "8880"))
    uvicorn.run("capsize_social.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
