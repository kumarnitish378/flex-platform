"""Generate the Dart API client from `api-spec.yaml` (A02, ADR-0009).

The spec is the contract: change it first, regenerate, then implement. That only works
if regenerating is one command that anybody can run, so this script finds its own Java,
caches the generator, and leaves the result in a reviewable state.

Two things worth knowing about where the output goes.

* The generated client is a **package**, not a folder of files: `dart-dio` emits its own
  `pubspec.yaml` and needs `build_runner` run inside it for the `built_value`
  serialisers. A `pubspec.yaml` nested under `app/lib/` would break the app's own
  package, so it lives at `app/packages/smart_cab_api/` and the app depends on it by
  path. `app/lib/data/api/` holds the hand-written wrapper - the auth interceptor and
  the repositories - which is the part anyone should actually read.
* Generated code is **not** linted or hand-edited (`coding-standards.md` section 3
  rule 3). The app's `analysis_options.yaml` excludes it.

Java comes from `JAVA_HOME`, then Android Studio's bundled JBR, then `PATH`. Android
Studio ships a JDK and this project already requires it for Android builds, so asking a
developer to install a second one would be rude.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs" / "03-architecture" / "api-spec.yaml"
OUTPUT = ROOT / "app" / "packages" / "smart_cab_api"

#: Pinned, because a generator that changes under us regenerates a different client from
#: the same spec - and then the diff is the generator's, not ours.
GENERATOR_VERSION = "7.17.0"
GENERATOR_URL = (
    "https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/"
    f"{GENERATOR_VERSION}/openapi-generator-cli-{GENERATOR_VERSION}.jar"
)
CACHE = ROOT / ".tooling"
JAR = CACHE / f"openapi-generator-cli-{GENERATOR_VERSION}.jar"

FLUTTER_CANDIDATES = (
    Path.home() / "flutter" / "bin",
    Path("C:/flutter/bin"),
)


def java() -> str:
    """A JDK, preferring the one Android Studio already installed."""
    if os.environ.get("JAVA_HOME"):
        candidate = Path(os.environ["JAVA_HOME"]) / "bin" / "java.exe"
        if candidate.exists():
            return str(candidate)
        candidate = Path(os.environ["JAVA_HOME"]) / "bin" / "java"
        if candidate.exists():
            return str(candidate)

    for studio in (
        Path("C:/Program Files/Android/Android Studio/jbr/bin/java.exe"),
        Path.home() / "AppData/Local/Programs/Android Studio/jbr/bin/java.exe",
    ):
        if studio.exists():
            return str(studio)

    found = shutil.which("java")
    if found:
        return found
    sys.exit(
        "no Java found. openapi-generator needs a JDK; Android Studio ships one at "
        "<studio>/jbr, or set JAVA_HOME."
    )


def flutter() -> str:
    """The Flutter SDK's `dart`, for `pub get` and `build_runner` in the generated package."""
    found = shutil.which("dart")
    if found:
        return found
    for directory in FLUTTER_CANDIDATES:
        candidate = directory / ("dart.bat" if os.name == "nt" else "dart")
        if candidate.exists():
            return str(candidate)
    sys.exit("no `dart` found. Put the Flutter SDK's bin directory on PATH.")


def fetch_generator() -> Path:
    if JAR.exists():
        return JAR
    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"downloading openapi-generator {GENERATOR_VERSION} (once)...", flush=True)
    with urllib.request.urlopen(GENERATOR_URL) as response:  # noqa: S310 - pinned URL
        JAR.write_bytes(response.read())
    return JAR


def run(command: list[str], cwd: Path | None = None) -> None:
    print("$ " + " ".join(command), flush=True)
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def generate() -> None:
    if not SPEC.exists():
        sys.exit(f"no spec at {SPEC}")

    jar = fetch_generator()
    # Wiped first: a stale model whose schema was deleted from the spec would otherwise
    # linger and still compile, which is drift the generator cannot see.
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    run(
        [
            java(),
            "-jar",
            str(jar),
            "generate",
            "-i",
            # Forward slashes: the generator parses this as a URI, and a Windows
            # `D:\...` path fails validation with "illegal character in opaque part".
            SPEC.as_posix(),
            "-g",
            "dart-dio",
            "-o",
            OUTPUT.as_posix(),
            "--additional-properties",
            ",".join(
                [
                    "pubName=smart_cab_api",
                    "pubVersion=0.1.0",
                    "pubDescription=Generated from api-spec.yaml. Do not edit by hand (ADR-0009).",
                    "serializationLibrary=built_value",
                ]
            ),
            "--global-property",
            # No docs or tests: the spec is the documentation, and generated tests assert
            # the generator works rather than that our product does.
            "modelDocs=false,apiDocs=false,modelTests=false,apiTests=false",
        ]
    )

    dart = flutter()
    run([dart, "pub", "get"], cwd=OUTPUT)
    run(
        [
            dart,
            "run",
            "build_runner",
            "build",
            "--delete-conflicting-outputs",
            # JIT, not AOT. `build_runner` precompiles its build script with
            # `gen_snapshot.exe`, which Windows Application Control blocks on this
            # machine - the same policy that blocks mypy's compiled wheel. JIT costs a
            # few seconds per run and produces identical output, so it is the default
            # rather than a workaround somebody has to rediscover.
            "--force-jit",
        ],
        cwd=OUTPUT,
    )
    print(f"\ngenerated {OUTPUT.relative_to(ROOT)}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="only report whether the prerequisites are present",
    )
    args = parser.parse_args()

    if args.check:
        print(f"spec:      {SPEC} {'found' if SPEC.exists() else 'MISSING'}")
        print(f"java:      {java()}")
        print(f"dart:      {flutter()}")
        print(f"generator: {'cached' if JAR.exists() else 'will download'}")
        return 0

    generate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
