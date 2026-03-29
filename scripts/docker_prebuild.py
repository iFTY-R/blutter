#!/usr/bin/python3
import argparse
import os
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from blutter import BlutterInput, cmake_blutter
from dartvm_fetch_build import DartLibInfo, fetch_and_build


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def parse_targets(raw_targets: str, default_os: str, default_arch: str):
    targets = []
    seen = set()
    for item in raw_targets.split(","):
        item = item.strip()
        if not item:
            continue

        parts = item.split("_")
        if len(parts) == 1:
            version = parts[0]
            os_name = default_os
            arch = default_arch
        elif len(parts) == 3:
            version, os_name, arch = parts
        else:
            raise ValueError(
                f"Invalid target '{item}'. Use VERSION or VERSION_OS_ARCH."
            )

        key = (version, os_name, arch)
        if key not in seen:
            seen.add(key)
            targets.append(key)

    return targets


def build_target(version: str, os_name: str, arch: str, compressed_ptrs: bool, with_no_analysis: bool):
    info = DartLibInfo(version, os_name, arch, has_compressed_ptrs=compressed_ptrs)
    print(
        "Prebuilding target:",
        f"version={version}",
        f"os={os_name}",
        f"arch={arch}",
        f"compressed_ptrs={compressed_ptrs}",
        f"with_no_analysis={with_no_analysis}",
    )

    fetch_and_build(info)

    default_input = BlutterInput("", info, ROOT_DIR, True, False, False)
    cmake_blutter(default_input)

    if with_no_analysis and not default_input.no_analysis:
        no_analysis_input = BlutterInput("", info, ROOT_DIR, True, False, True)
        cmake_blutter(no_analysis_input)


def main():
    parser = argparse.ArgumentParser(
        description="Prebuild selected blutter targets into the Docker image."
    )
    parser.add_argument(
        "--targets",
        default=os.getenv("PREBUILD_TARGETS", ""),
        help="Comma-separated targets in VERSION or VERSION_OS_ARCH format.",
    )
    parser.add_argument(
        "--default-os",
        default=os.getenv("PREBUILD_DEFAULT_OS", "android"),
        help="Default target OS used when only VERSION is provided.",
    )
    parser.add_argument(
        "--default-arch",
        default=os.getenv("PREBUILD_DEFAULT_ARCH", "arm64"),
        help="Default target arch used when only VERSION is provided.",
    )
    parser.add_argument(
        "--with-no-analysis",
        action="store_true",
        default=env_flag("PREBUILD_WITH_NO_ANALYSIS", False),
        help="Also prebuild the --no-analysis blutter binary.",
    )
    parser.add_argument(
        "--no-compressed-ptrs",
        dest="compressed_ptrs",
        action="store_false",
        default=env_flag("PREBUILD_COMPRESSED_PTRS", True),
        help="Prebuild using non-compressed pointers instead of the default compressed pointers.",
    )
    args = parser.parse_args()

    if not args.targets.strip():
        print("PREBUILD_TARGETS is empty; skipping prebuild.")
        return

    for version, os_name, arch in parse_targets(
        args.targets, args.default_os, args.default_arch
    ):
        build_target(
            version,
            os_name,
            arch,
            compressed_ptrs=args.compressed_ptrs,
            with_no_analysis=args.with_no_analysis,
        )


if __name__ == "__main__":
    main()
