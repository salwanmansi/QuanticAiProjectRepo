import os

# Bind to the port provided by the hosting environment (Render, etc.)
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

workers = 1
threads = 2
timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"