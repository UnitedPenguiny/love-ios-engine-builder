"""Build an unsigned, generic LÖVE iOS engine. No game or credentials needed."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile

SOURCE_URL = "https://github.com/love2d/love/releases/download/11.5/love-11.5-ios-source.zip"
SOURCE_SHA256 = "8a72a3239a4ae7092aa5087c86e5cb2dfc6ce808b1c189e2d4ea1b91db6cb035"


def prepare(source):
    plist_path = source / "platform/xcode/ios/love-ios.plist"
    with plist_path.open("rb") as stream:
        info = plistlib.load(stream)
    info.update(CFBundleDisplayName="Pocket LOVE", UIRequiresFullScreen=True,
                UIStatusBarHidden=True, UIFileSharingEnabled=True,
                ITSAppUsesNonExemptEncryption=False)
    orientations = ["UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"]
    info["UISupportedInterfaceOrientations"] = orientations
    info["UISupportedInterfaceOrientations~ipad"] = orientations
    for key in ("CFBundleDocumentTypes", "UTExportedTypeDeclarations"):
        info.pop(key, None)
    with plist_path.open("wb") as stream:
        plistlib.dump(info, stream)
    return plist_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, help="Existing official source for local inspection")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="love-ios-") as temporary:
        # macOS /var is a symlink to /private/var: compare canonical paths.
        work = Path(temporary).resolve()
        if args.source:
            source = args.source.resolve()
        else:
            archive = work / "source.zip"
            urllib.request.urlretrieve(SOURCE_URL, archive)
            with archive.open("rb") as stream:
                assert hashlib.file_digest(stream, "sha256").hexdigest() == SOURCE_SHA256, "Upstream download hash mismatch"
            with zipfile.ZipFile(archive) as bundle:
                for entry in bundle.infolist():
                    assert (work / entry.filename).resolve().is_relative_to(work), "Unsafe source path"
                bundle.extractall(work)
            source = work / "love-11.5-ios-source"
        prepare(source)
        command = ["xcodebuild", "-project", str(source / "platform/xcode/love.xcodeproj"),
                   "-target", "love-ios", "-configuration", "Release", "-sdk", "iphoneos",
                   "-arch", "arm64", "ONLY_ACTIVE_ARCH=NO", "CODE_SIGNING_ALLOWED=NO",
                   "CODE_SIGNING_REQUIRED=NO", "CODE_SIGN_IDENTITY=", "ENABLE_BITCODE=NO",
                   "IPHONEOS_DEPLOYMENT_TARGET=13.0", "PRODUCT_BUNDLE_IDENTIFIER=org.love2d.pocketengine",
                   "CONFIGURATION_BUILD_DIR=" + str(work / "Build")]
        if args.prepare_only:
            print(json.dumps({"prepared": str(source), "build_command": command}))
            return
        if shutil.which("xcodebuild") is None:
            raise SystemExit("Xcode is required on the build machine. Use the public macOS workflow from Windows.")
        subprocess.run(["xcodebuild", "-version"], check=True)
        subprocess.run(command, check=True)
        app = work / "Build/love.app"
        assert (app / "love").is_file(), "Expected iOS executable was not produced"
        subprocess.run(["xcrun", "lipo", str(app / "love"), "-verify_arch", "arm64"], check=True)
        with (app / "Info.plist").open("rb") as stream:
            assert plistlib.load(stream)["CFBundleSupportedPlatforms"] == ["iPhoneOS"]
        destination = output / "love-ios-engine.ipa"
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(app.rglob("*")):
                if path.is_file():
                    bundle.write(path, "Payload/love.app/" + path.relative_to(app).as_posix())
        report = {"love_version": "11.5", "source_url": SOURCE_URL,
                  "source_sha256": SOURCE_SHA256, "signed": False, "contains_game": False,
                  "bytes": destination.stat().st_size,
                  "sha256": hashlib.file_digest(destination.open("rb"), "sha256").hexdigest()}
        (output / "engine-build.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
        print(json.dumps(report))


if __name__ == "__main__":
    main()
