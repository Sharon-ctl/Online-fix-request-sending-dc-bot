import asyncio
import os
import signal
import sys
from config import Config
from utils.logger import log
from utils.exceptions import ConfigurationError
from bot import OnlineFixBot

async def main():
    try:
        # Validate config before starting
        Config.validate()
        log.info("action=startup msg=Configuration validated")
    except ConfigurationError as e:
        log.critical(f"action=startup_failed error={e}")
        sys.exit(1)

    bot = OnlineFixBot()

    # Handle graceful shutdown signals (SIGINT, SIGTERM)
    # Note: Windows support for asyncio signals is limited, but this works on Linux/Docker
    if os.name != "nt":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, lambda: asyncio.create_task(shutdown(bot, sig))
            )
            
    try:
        await bot.start(Config.BOT_TOKEN)
    except Exception as e:
        log.critical(f"action=bot_crash error={e}")
    finally:
        if not bot.is_closed():
            await bot.close()

async def shutdown(bot, sig):
    """Signal handler for graceful shutdown."""
    log.info(f"action=signal_received signal={sig.name}")
    await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("action=keyboard_interrupt msg=Shutting down gracefully")
