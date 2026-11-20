# Workspace File Map

**Inspection date:** 2026-11-19. Workspace exists at `C:\Users\PC\linux-desktop`; Git check failed (`fatal: not a git repository`). No commit/push.

## Root documentation

| Path | Purpose / current status |
|---|---|
| `README.md` | Vietnamese project summary. Current text records M1 NOT VERIFIED, M2 NOT STARTED, the limited manual XFCE evidence, snapshot path, no cold-start claim. |
| `INSTALL_REPORT.md` | Long historical installation and device report. Contains old manager-blocked claims plus prior install history; reconcile contradictions against `TEST_REPORT.md` and this handoff. |
| `TEST_REPORT.md` | Historical test results and 2026-11-19 M1/M2 pivot/addendum. Contains earlier GUI acceptance and lifecycle history; distinguish legacy table from current project status. |
| `TROUBLESHOOTING.md` | Warnings about manager, PRoot/cgroups, Mesa software-rendering workaround, recovery boundaries. Some older sections precede successful manual XFCE run. |
| `LIFECYCLE_AUDIT.md` | Threat/ownership analysis of legacy process manager and ADB/Termux observations. Historical and implementation-specific; important warning not to deploy manager. |
| `handoff/claude-to-codex/*.md` | This technical handoff package; created 2026-11-19, local documentation only. |

## Scripts

| Path | Purpose / status |
|---|---|
| `scripts/desktop.py` | Legacy Python lifecycle manager (`start`, `stop`, `status`, `resume` in current file); complex PRoot/X11/process ownership, state, PIDFD and probe logic. Not proven safe end-to-end; do not run on tablet. See `KNOWN_ISSUES.md`. |
| `scripts/start-linux.sh` | Thin wrapper executing `desktop.py start`; no independent lifecycle safeguards. |
| `scripts/stop-linux.sh` | Thin wrapper executing `desktop.py stop`; do not use for active unknown sessions. |
| `scripts/status-linux.sh` | Thin wrapper executing `desktop.py status`; even status may interact with manager runtime/lock logic, see source. |
| `scripts/xfce-components.sh` | Component-run experiment; different XDG config path from verified session and trap sends TERM to children. Do not start on current `:2`. |
| `scripts/minimal-launcher/linux-resume.sh` | Resume-only Termux shell script. Source is 5.2 KB; device copy verified. Validates existing XFCE session and opens viewer; no cold start. |
| `scripts/__pycache__/desktop.cpython-312.pyc`, `cpython-313.pyc` | Python cache artifacts; not source of truth. |

## Tests

| Path | Purpose / status |
|---|---|
| `tests/test_lifecycle.py` | Python lifecycle tests with fake processes/temp dirs; contains experiments and contracts not aligned to current manager source. Includes duplicate `if __name__ == '__main__'` block. Not run in this handoff. |
| `tests/test_manager_security.py` | Three focused manager security tests using mocks. Not run in this handoff. |
| `tests/__pycache__/*` | Python test bytecode cache. |

No `pytest.ini`, `pyproject.toml`, tox config or other test framework files were confirmed in top-level inventory. No test run in this handoff. Historical report mentions earlier test results; see `KNOWN_ISSUES.md` for contradictions.

## Android Kotlin project

| Path | Purpose / status |
|---|---|
| `android/settings.gradle.kts`, `android/build.gradle.kts` | Gradle project settings/build plugin setup. |
| `android/app/build.gradle.kts` | App build config; package id/source details should be checked before any future build/release. |
| `android/app/src/main/AndroidManifest.xml` | Requests Termux RUN_COMMAND; launcher MainActivity is exported; ResultReceiver is non-exported. |
| `android/app/src/main/java/dev/local/linuxdesktop/launcher/MainActivity.kt` | UI with status/start/stop/resume/permission handling and launch flow reconciliation. Current configured command paths point to `$HOME/.local/linux-desktop/{start,stop,status}-linux.sh`, whereas current project wrappers sit in `scripts/`; this mismatch is a deployment blocker. |
| `android/app/src/main/java/dev/local/linuxdesktop/launcher/TermuxCommands.kt` | Termux `RUN_COMMAND` service invocation, mutable one-shot callback, timeout and result parsing. |
| `android/app/src/main/java/dev/local/linuxdesktop/launcher/CommandResult.kt` | Command outcome/state helper. |
| `android/app/src/test/java/dev/local/linuxdesktop/launcher/CommandResultTest.kt` | Unit test source. |
| `android/app/src/main/res/drawable/ic_launcher.xml` | Android vector launcher icon. |
| `android/app/build/outputs/apk/debug/app-debug.apk` | Debug build artifact exists (~839 KB at inventory); not installed on device. It is not a validated release package. |
| `android/app/build/outputs/apk/debug/output-metadata.json` | Build metadata. |
| `android/app/build/outputs/logs/manifest-merger-debug-report.txt` | Manifest merge output. |
| `android/.gradle-user`, `.gradle`, `build`, `.kotlin`, `tmp*`, `.tmp-loader.apk`, `.tmp-wrapper` | Build caches and temporary artifacts. Preserve; do not treat caches as source. Do not delete without authorization. |

The app currently uses fixed Termux paths and action enum `START`, `STOP`, `STATUS`; no `RESUME` command enum. Manifest declares exported launcher Activity. Source not installed on Android; no APK rebuild/installation was performed in this handoff.

## Snapshot/config and icon assets

| Path | Purpose / status |
|---|---|
| `snapshots/xfce-config-20261119T103201/xfce-config.snapshot.tar` | Single saved-XFCE-config archive. SHA-256 `debf6dc6510598e9044bc3b1fe54d034613d3a1711d9f958c014264a8c31ce13`. Contains config XML and Thunar/panel files, no live runtime/cache/socket. Not an atomic snapshot. |
| `android/app/src/main/res/drawable/ic_launcher.xml` | Standalone app icon vector. |
| `C:\Users\PC\AppData\Local\Temp\linux-desktop-icon.png` | Earlier generated 192×192 dark/teal/white-L icon; local temp path, not confirmed inside project. Device copy is in Termux shortcut icon path. |

Snapshot contents include `Thunar/accels.scm`, `Thunar/uca.xml`, XFCE desktop/panel launcher files, and XFCE xfconf channel XML (`displays.xml`, `thunar.xml`, `xfce4-appfinder.xml`, `xfce4-desktop.xml`, `xfce4-keyboard-shortcuts.xml`, `xfce4-panel.xml`, `xfwm4.xml`, `xsettings.xml`).

## Files intentionally absent / unknown

- No `handoff/claude-to-codex/` existed before this task; created during this handoff.
- No source APK package is installed on tablet (`dev.local.linuxdesktop.launcher` absent).
- No additional `.py`, `.sh`, `.kt` source files were found beyond those listed; Android build/cache tree is large and was excluded from source listing.
- No Git metadata, so dirty/clean working tree cannot be reported; it is a non-Git workspace.
