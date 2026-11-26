"""Shared pytest settings. Run tests per lab (``python run_all.py --tests`` does this),
because every lab has its own ``server.py`` and ``test_lab.py``."""
import os

os.environ["GENUX_STREAM_DELAY"] = "0"
os.environ.pop("GENUX_LIVE", None)  # tests never call a real model
