import argparse
from pathlib import Path

import uvicorn

from file_manager.core.config import settings


def main():

    parser = argparse.ArgumentParser(
        description="Remote filesystem server."
    )

    parser.add_argument(
        "-root",
        type=str,
        nargs="+",
        required=True,
        help="Root directory (or directories) accessible through the server."
    )

    parser.add_argument(
        "-host",
        type=str,
        default="0.0.0.0",
        help="Server host."
    )

    parser.add_argument(
        "-port",
        type=int,
        default=settings.port,
        help="Server port."
    )

    parser.add_argument(
        "-password",
        type=str,
        default="PeergosRules!",
        help="Authentication password."
    )

    parser.add_argument(
        "-debug",
        action="store_true",
        help="Enable debug mode."
    )

    args = parser.parse_args()

    roots = [Path(r).resolve() for r in args.root]

    for r in roots:
        if not r.exists():
            raise RuntimeError(f"Root directory does not exist: {r}")
        if not r.is_dir():
            raise RuntimeError(f"Root path is not a directory: {r}")

    if len(roots) == 1:
        settings.root = roots[0]
    else:
        import tempfile
        import atexit
        import shutil
        import _winapi

        tmp_dir = Path(tempfile.mkdtemp(prefix="fm_virtual_root_"))
        
        # Cleanup the temp directory on exit
        atexit.register(lambda: shutil.rmtree(tmp_dir, ignore_errors=True))

        for r in roots:
            link_path = tmp_dir / r.name
            
            # Handle duplicate folder names by appending an index
            if link_path.exists():
                link_path = tmp_dir / f"{r.name}_{roots.index(r)}"
                
            _winapi.CreateJunction(str(r), str(link_path))

        settings.root = tmp_dir
    settings.password = args.password
    settings.host = args.host
    settings.port = args.port
    settings.debug = args.debug

    print(
        f"Filesystem root: {settings.root}"
    )

    uvicorn.run(
        "file_manager.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )


if __name__ == "__main__":
    main()