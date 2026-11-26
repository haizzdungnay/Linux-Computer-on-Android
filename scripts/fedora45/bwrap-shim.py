#!/usr/bin/python3
"""PRoot compatibility shim for bwrap used by Fedora 45 glycin image loaders."""
import os
import sys


def main():
    args = sys.argv[1:]
    env = os.environ.copy()
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            i += 1
            break
        if a in ("--ro-bind", "--ro-bind-try", "--bind", "--bind-try", "--symlink", "--setenv", "--dev-bind", "--dev-bind-try", "--chmod"):
            if a == "--setenv" and i + 2 < len(args):
                env[args[i + 1]] = args[i + 2]
            i += 3
        elif a in ("--chdir", "--tmpfs", "--dev", "--proc", "--seccomp", "--perms", "--dir", "--unsetenv", "--remount-ro", "--ro-bind-data", "--bind-data", "--file", "--infofd", "--json-status-fd", "--sync-fd", "--block-fd", "--userns-block-fd", "--info-fd", "--uid", "--gid", "--hostname"):
            if a == "--unsetenv" and i + 1 < len(args):
                env.pop(args[i + 1], None)
            i += 2
        elif a.startswith("--"):
            i += 1
        else:
            break
    if i >= len(args):
        return 1
    cmd = args[i:]
    if cmd[0] in ("/usr/bin/true", "/bin/true", "true"):
        sys.stderr.write("bwrap: setting up uid map: Permission denied\n")
        return 1
    os.execvpe(cmd[0], cmd, env)


if __name__ == "__main__":
    raise SystemExit(main())
