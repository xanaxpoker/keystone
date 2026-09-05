#!/usr/bin/env bash
set -euo pipefail
arch="${1:?Expected arm64 or x86_64}"
case "$arch" in arm64|x86_64) ;; *) exit 2 ;; esac
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
stage="$root/build/package-$arch"
mkdir -p "$stage" dist
cmake --install build --prefix "$stage"
app="$stage/Keystone.app"
test -d "$app"
lipo -verify_arch "$arch" "$app/Contents/MacOS/Keystone"
# Nested code is signed first; never use the upstream developer identity.
while IFS= read -r -d '' binary; do
  if file "$binary" | grep -q 'Mach-O'; then codesign --force --sign - "$binary"; fi
done < <(find "$app" -type f -print0)
codesign --force --deep --sign - "$app"
codesign --verify --deep --strict "$app"
# All dynamic dependencies must be self-contained or macOS system libraries.
python3 utils/verify-macos-bundle.py "$app" "$arch"
cp KEYSTONE.md COPYING LICENSE.* "$stage/"
ln -s /Applications "$stage/Applications"
hdiutil create -volname "Keystone" -srcfolder "$stage" -ov -format UDZO "dist/Keystone-preview-$arch.dmg"
shasum -a 256 "dist/Keystone-preview-$arch.dmg" > "dist/Keystone-preview-$arch.dmg.sha256"
