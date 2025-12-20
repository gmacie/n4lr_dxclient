# Simple page-level pubsub bridge between backend tasks and UI.

_page = None
_callback = None

def init_pubsub(page):
    """Call once from run.py before building MainUI."""
    global _page
    _page = page

    # Flet 0.28.x: page.create_pubsub() creates a PubSub channel.
    if not hasattr(page, "pubsub") or page.pubsub is None:
        page.pubsub = page.create_pubsub()

    # Subscribe dispatcher
    page.pubsub.subscribe(_dispatch)

def register_callback(cb):
    """UI registers a function that receives messages (dicts)."""
    global _callback
    _callback = cb

def publish(msg: dict):
    """Backend sends messages to UI."""
    if _page and hasattr(_page, "pubsub") and _page.pubsub:
        _page.pubsub.send_all(msg)

def _dispatch(msg):
    """Deliver messages from pubsub to the UI callback."""
    if _callback:
        _callback(msg)
