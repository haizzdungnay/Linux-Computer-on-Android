package dev.local.linuxdesktop.launcher

import java.io.File

/** Pure builder for PRoot invocation arguments and isolated environment variables. */
object ProotCommandBuilder {
    private const val GUEST_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

    fun buildArgs(
        prootBin: File,
        rootfsDir: File,
        tmpDir: File,
        guestCommand: String,
    ): List<String> = listOf(
        prootBin.absolutePath,
        "--link2symlink",
        "-L",
        "--kill-on-exit",
        "-0",
        "-r", rootfsDir.absolutePath,
        "-b", "/dev",
        "-b", "/proc",
        "-b", "/sys",
        "-b", "${tmpDir.absolutePath}:/tmp",
        "-b", "/dev/urandom:/dev/random",
        "-w", "/root",
        "/usr/bin/env", "-i",
        "HOME=/root",
        "TERM=xterm-256color",
        "LANG=C.UTF-8",
        "PATH=$GUEST_PATH",
        "DISPLAY=:2",
        "XDG_CONFIG_HOME=/root/.ld-test/xfce-config",
        "LIBGL_ALWAYS_SOFTWARE=1",
        "GALLIUM_DRIVER=llvmpipe",
        "/bin/sh", "-c", guestCommand,
    )

    fun buildEnv(nativeLibDir: File, libDir: File, tmpDir: File): Map<String, String> = mapOf(
        "PROOT_LOADER" to File(nativeLibDir, "libproot-loader.so").absolutePath,
        "PROOT_LOADER_32" to File(nativeLibDir, "libproot-loader32.so").absolutePath,
        "PROOT_TMP_DIR" to tmpDir.absolutePath,
        "LD_LIBRARY_PATH" to "${libDir.absolutePath}:${nativeLibDir.absolutePath}",
        "TMPDIR" to tmpDir.absolutePath,
    )
}
