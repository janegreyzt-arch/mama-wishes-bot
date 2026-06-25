import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
    force=True,
)

try:
    from bot import main
except Exception:
    logging.exception("Ошибка при загрузке бота")
    raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        logging.exception("Бот остановлен с ошибкой")
        raise
