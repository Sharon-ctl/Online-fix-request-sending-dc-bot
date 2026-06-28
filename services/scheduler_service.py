import asyncio
from discord.ext import tasks
from utils.logger import log
from services.release_service import ReleaseService
from config import Config

class SchedulerService:
    def __init__(self, release_service: ReleaseService):
        self.release_service = release_service
        log.info(f"action=scheduler_init interval_minutes={Config.FETCH_INTERVAL_MINUTES}")

    def start(self):
        """Starts the background task loop."""
        if not self.daily_fetch.is_running():
            self.daily_fetch.start()
            log.info("action=scheduler_started")

    def stop(self):
        """Stops the background task loop."""
        if self.daily_fetch.is_running():
            self.daily_fetch.cancel()
            log.info("action=scheduler_stopped")

    # The decorator uses a dummy interval which is overridden in start if needed, 
    # but we can just use Config dynamically directly because tasks.loop allows dynamic injection if we define it properly.
    # However, passing Config.FETCH_INTERVAL_MINUTES directly at module load time is safe because Config is loaded at import time.
    @tasks.loop(minutes=Config.FETCH_INTERVAL_MINUTES)
    async def daily_fetch(self):
        """The actual task that runs at the scheduled interval."""
        log.info("action=interval_fetch_triggered")
        await self.release_service.check_and_post_new_releases()

    @daily_fetch.before_loop
    async def before_daily_fetch(self):
        """Wait until the bot is ready before starting the loop."""
        log.info("action=scheduler_waiting_for_ready")
        await asyncio.sleep(5)  # Small delay to ensure everything is fully loaded
