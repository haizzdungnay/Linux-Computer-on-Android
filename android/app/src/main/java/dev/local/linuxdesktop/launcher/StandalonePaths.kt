package dev.local.linuxdesktop.launcher

import android.content.Context
import java.io.File

/** Paths inside the app sandbox for standalone PRoot Debian + X11 runtime. */
class StandalonePaths(context: Context) {
    val baseDir = File(context.filesDir, "linux-desktop")
    val rootfsDir = File(baseDir, "debian/rootfs")
    val tmpDir = File(baseDir, "tmp")
    val x11UnixDir = File(tmpDir, ".X11-unix")
    val x11Socket = File(x11UnixDir, "X2")
    val libDir = File(baseDir, "lib")
    val tallocLib = File(libDir, "libtalloc.so.2")
    val downloadArchive = File(baseDir, "debian-trixie-arm64.tar.xz")
    val installLog = File(baseDir, "install.log")
    val sessionLog = File(baseDir, "session.log")
    val installedMarker = File(baseDir, ".installed-ok")
    val nativeLibDir = File(context.applicationInfo.nativeLibraryDir)

    val debianAppDir = File(rootfsDir, "root/.local/share/linux-desktop")
    val debianPicomDir = File(debianAppDir, "picom-xfce")
    val debianApplicationsDir = File(rootfsDir, "root/.local/share/applications")
    val debianProfileDir = File(rootfsDir, "root/.ld-test/xfce-config")
    val debianXkbDir = File(rootfsDir, "usr/share/X11/xkb")

    fun ensureDirs() {
        baseDir.mkdirs()
        rootfsDir.mkdirs()
        tmpDir.mkdirs()
        x11UnixDir.mkdirs()
        libDir.mkdirs()
    }
}
