from __future__ import annotations

import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo


def main() -> None:
    now = datetime.now(ZoneInfo("America/Toronto"))
    if now.weekday() == 0 and now.hour == 9:
        subprocess.run(["film-agent", "run-weekly", "--live"], check=True)
    else:
        print(f"Skipping scheduled run at {now.isoformat()}")


if __name__ == "__main__":
    main()
