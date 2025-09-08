import os
from app import app
import routes  # noqa: F401
import scheduler

if __name__ == "__main__":
    # Start the background scheduler for Meta API sync
    scheduler.start_scheduler()
    
    # Use PORT environment variable for Railway, fallback to 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    app.run(host="0.0.0.0", port=port, debug=debug)
