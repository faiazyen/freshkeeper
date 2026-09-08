"""Start the FreshKeeper web server.

    python scripts/run_server.py [--db data/demo.db] [--port 5000] [--live]

The bearer token is printed at startup. Pass --token to fix it instead, which
is what the screenshot script does so it can log in.

``--live`` attaches the simulated sensor backend and starts the background
acquisition scheduler, so the interface updates on its own. Without it the
server just serves whatever is already in the database, which is what the
screenshot pass wants.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from freshkeeper.api.app import create_app  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/demo.db")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--token", default=None,
                        help="bearer token; a random one is generated if omitted")
    parser.add_argument("--live", action="store_true",
                        help="attach the simulated backend and run cycles")
    args = parser.parse_args()

    service = None
    if args.live:
        from freshkeeper.db.session import make_engine, make_session_factory
        from freshkeeper.hardware.sim_backend import SimulatedSensorBackend
        from freshkeeper.ml.inference import InferenceService
        factory = make_session_factory(make_engine(args.db))
        service = InferenceService(SimulatedSensorBackend(time_acceleration=6.0),
                                   factory)

    app = create_app(args.db, auth_token=args.token, inference_service=service)
    # Print the token that is actually in use. When --token is omitted the app
    # generates a random one, which is the behaviour the thesis describes; the
    # old default of "devtoken" meant it never did.
    print(f"FreshKeeper on http://{args.host}:{args.port}")
    print(f"  token: {app.config['AUTH_TOKEN']}")
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
