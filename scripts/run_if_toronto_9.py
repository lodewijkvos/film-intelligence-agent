from __future__ import annotations

import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo


def main() -> None:
    now = datetime.now(ZoneInfo("America/Toronto"))
    if now.weekday() != 0 or now.hour != 9:
        print(f"Skipping run at {now.isoformat()} because it is not Monday 9:00 America/Toronto.")
        return
    subprocess.run(["film-intel", "run-weekly", "--live"], check=True)


if __name__ == "__main__":
    main()
