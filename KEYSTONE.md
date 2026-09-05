# Keystone

A macOS-focused interface fork of KeePassXC 2.7.12, inspired by the clarity of Apple Passwords. Working brand: Keystone.

The fork retains KeePassXC copyright notices and GPL licensing. It is independent of KeePassXC and Apple. Source and license files must accompany distribution as required by those licenses.

## Changes

Three-column vault / entries / details layout, vertically arranged credential fields, more readable list spacing, blue accent, light/dark styling, new welcome flow and icon. Existing entry editing, reveal controls, clipboard handling, locking, KDBX readers/writers, cryptography and key derivation remain upstream implementations. This is not a new security audit or a claim of equivalent validation.

## Build

The macOS workflow builds separately on native ARM64 and x86_64 runners using pinned vcpkg dependencies. It runs upstream tests before creating ad-hoc signed DMGs. Those builds are development previews, not Developer ID signed/notarized releases. Browser integration and hardware unlock require separate end-to-end verification after rebranding. Automatic upstream update checks are disabled for the fork.

Local checkout: /Applications/sidetabs/Coding/keystone

Keystone uses separate single-instance and browser IPC endpoint names so the fork can run alongside KeePassXC. The browser message format, pairing and encryption remain upstream implementations.
