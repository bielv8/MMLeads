from app import app
import routes  # noqa: F401
import scheduler

if __name__ == "__main__":
    # Start the background scheduler for Meta API sync
    scheduler.start_scheduler()
    app.run(host="0.0.0.0", port=5000, debug=True)
