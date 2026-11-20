package dev.local.linuxdesktop.launcher

import android.content.Context
import android.system.Os
import org.apache.commons.compress.archivers.tar.TarArchiveEntry
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream
import org.tukaani.xz.XZInputStream
import java.io.BufferedInputStream
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL

/** Downloads Debian 13 ARM64 rootfs, extracts it safely, and provisions XFCE + WhiteSur + scripts. */
class RootfsInstaller(private val context: Context) {
    private val paths = StandalonePaths(context)
    private val runner = ProotRunner(context, paths)

    data class Progress(val step: String, val percent: Int, val detail: String)

    fun isInstalled(): Boolean = paths.installedMarker.isFile &&
        File(paths.rootfsDir, "usr/bin/xfce4-session").isFile

    fun install(onProgress: (Progress) -> Unit, onLog: (String) -> Unit) {
        paths.ensureDirs()
        paths.installedMarker.delete()
        paths.installLog.writeText("")

        fun log(msg: String) {
            paths.installLog.appendText("$msg\n")
            onLog(msg)
        }

        onProgress(Progress("Resolving Debian 13 ARM64 image...", 5, ""))
        val indexHtml = fetchText(RootfsCatalog.INDEX_URL)
        val rootfsUrl = RootfsCatalog.latestTrixieRootfsUrl(indexHtml)
        log("Rootfs URL: $rootfsUrl")

        onProgress(Progress("Downloading Debian 13 rootfs...", 10, ""))
        downloadFile(rootfsUrl, paths.downloadArchive) { done, total ->
            val pct = if (total > 0) 10 + ((done * 25) / total).toInt() else 20
            val mbDone = done / (1024 * 1024)
            val mbTotal = if (total > 0) "${total / (1024 * 1024)} MB" else "?"
            onProgress(Progress("Downloading Debian 13 rootfs...", pct, "$mbDone / $mbTotal MB"))
        }
        log("Downloaded rootfs archive (${paths.downloadArchive.length() / (1024 * 1024)} MB)")

        onProgress(Progress("Extracting Debian rootfs...", 36, "Unpacking tar.xz"))
        extractTarXz(paths.downloadArchive, paths.rootfsDir)
        paths.downloadArchive.delete()
        log("Extracted rootfs into ${paths.rootfsDir.absolutePath}")

        onProgress(Progress("Deploying workstation scripts...", 50, ""))
        deployAssetsAndBaseConfig()
        configureX11Defaults()
        log("Deployed scripts and X11 defaults")

        onProgress(Progress("Installing XFCE, Picom, Firefox (apt-get)...", 55, "This may take several minutes"))
        val aptCmd = """
            set -eu
            export DEBIAN_FRONTEND=noninteractive
            mkdir -p /tmp /var/tmp /run/dbus
            chmod 1777 /tmp /var/tmp
            apt-get update
            apt-get install -y --no-install-recommends \
                xfce4 xfce4-whiskermenu-plugin xfce4-clipman-plugin xfce4-genmon-plugin \
                dbus-x11 x11-utils x11-xserver-utils picom firefox-esr \
                mousepad thunar xfce4-terminal \
                fonts-noto-core fonts-noto-mono kf6-breeze-icon-theme \
                sassc git curl python3 ca-certificates
            apt-get clean
        """.trimIndent()
        val aptExit = runner.runAndStream(aptCmd) { line -> log(line) }
        if (aptExit != 0) throw IllegalStateException("apt-get failed with exit code $aptExit")

        onProgress(Progress("Installing WhiteSur themes, icons & wallpaper...", 82, ""))
        val themeCmd = """
            set -eu
            SRC=/root/.local/share/linux-desktop/sources
            mkdir -p "${'$'}SRC" /root/.themes /root/.local/share/icons /root/.local/share/backgrounds
            if [ ! -d "${'$'}SRC/WhiteSur-gtk-theme/.git" ]; then
                git clone --depth=1 https://github.com/vinceliuice/WhiteSur-gtk-theme.git "${'$'}SRC/WhiteSur-gtk-theme"
            fi
            if [ ! -d /root/.themes/WhiteSur-Dark ]; then
                "${'$'}SRC/WhiteSur-gtk-theme/install.sh" -d /root/.themes -c Dark -N glassy || true
            fi
            if [ ! -d "${'$'}SRC/WhiteSur-icon-theme/.git" ]; then
                git clone --depth=1 https://github.com/vinceliuice/WhiteSur-icon-theme.git "${'$'}SRC/WhiteSur-icon-theme"
            fi
            if [ ! -d /root/.local/share/icons/WhiteSur-dark ]; then
                "${'$'}SRC/WhiteSur-icon-theme/install.sh" -d /root/.local/share/icons || true
            fi
            if [ ! -f /root/.local/share/backgrounds/WhiteSur-Monterey.jpg ]; then
                curl -fsSL -o /root/.local/share/backgrounds/WhiteSur-Monterey.jpg \
                    https://raw.githubusercontent.com/vinceliuice/WhiteSur-wallpapers/main/2k/Monterey.jpg || true
            fi
            rm -rf "${'$'}SRC/WhiteSur-gtk-theme/.git" "${'$'}SRC/WhiteSur-icon-theme/.git"
        """.trimIndent()
        val themeExit = runner.runAndStream(themeCmd) { line -> log(line) }
        if (themeExit != 0) log("Theme setup exited with $themeExit (non-fatal fallback active)")

        onProgress(Progress("Configuring XFCE desktop defaults...", 92, ""))
        val xfceInitCmd = """
            set -eu
            export HOME=/root XDG_CONFIG_HOME=/root/.ld-test/xfce-config LANG=C.UTF-8
            mkdir -p "${'$'}XDG_CONFIG_HOME"
            dbus-run-session -- sh -ec '
                xfconf-query -c xsettings -p /Net/ThemeName -n -t string -s WhiteSur-Dark
                xfconf-query -c xsettings -p /Net/IconThemeName -n -t string -s WhiteSur-dark
                xfconf-query -c xsettings -p /Gtk/DecorationLayout -n -t string -s "close,minimize,maximize:"
                xfconf-query -c xsettings -p /Gtk/FontName -n -t string -s "Noto Sans 11"
                xfconf-query -c xsettings -p /Gtk/MonospaceFontName -n -t string -s "Noto Sans Mono 11"
                xfconf-query -c xsettings -p /Xft/DPI -n -t int -s 120
                xfconf-query -c xfwm4 -p /general/theme -n -t string -s WhiteSur-Dark
                xfconf-query -c xfwm4 -p /general/button_layout -n -t string -s "CHM|"
                xfconf-query -c xfwm4 -p /general/use_compositing -n -t bool -s false
                xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitorscreen/workspace0/last-image -n -t string -s /root/.local/share/backgrounds/WhiteSur-Monterey.jpg
                xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitorbuiltin/workspace0/last-image -n -t string -s /root/.local/share/backgrounds/WhiteSur-Monterey.jpg
            '
        """.trimIndent()
        val xfceExit = runner.runAndStream(xfceInitCmd) { line -> log(line) }
        if (xfceExit != 0) log("XFCE defaults exited with $xfceExit")

        paths.installedMarker.writeText("installed=${System.currentTimeMillis()}\n")
        onProgress(Progress("Installation complete!", 100, "Ready to launch"))
        log("Installation completed successfully.")
    }

    private fun deployAssetsAndBaseConfig() {
        val etcDir = File(paths.rootfsDir, "etc").apply { mkdirs() }
        File(etcDir, "resolv.conf").writeText("nameserver 1.1.1.1\nnameserver 8.8.8.8\n")
        File(etcDir, "hosts").writeText("127.0.0.1 localhost\n::1 localhost\n")
        val aptConfDir = File(etcDir, "apt/apt.conf.d").apply { mkdirs() }
        File(aptConfDir, "00proot").writeText(
            "APT::Sandbox::User \"root\";\n" +
                "DPkg::Options { \"--force-confdef\"; \"--force-confold\"; };\n"
        )

        paths.debianAppDir.mkdirs()
        paths.debianPicomDir.mkdirs()
        paths.debianApplicationsDir.mkdirs()
        File(paths.debianProfileDir, "gtk-3.0").mkdirs()

        val scriptNames = context.assets.list("scripts").orEmpty()
        for (name in scriptNames) {
            val target = when {
                name == "xfce-effects.py" -> File(paths.debianPicomDir, "xfce-effects.py")
                name == "picom-xrender.conf" -> File(paths.debianPicomDir, "picom.conf")
                name == "whitesur-panel.css" -> File(paths.debianProfileDir, "gtk-3.0/gtk.css")
                name.endsWith(".desktop") -> File(paths.debianApplicationsDir, name)
                else -> File(paths.debianAppDir, name)
            }
            context.assets.open("scripts/$name").use { input ->
                target.outputStream().use { output -> input.copyTo(output) }
            }
            val mode = if (name.endsWith(".sh") || name.endsWith(".py")) 0b111_101_101 else 0b110_100_100
            Os.chmod(target.absolutePath, mode)
        }
    }

    private fun configureX11Defaults() {
        val prefs = context.getSharedPreferences("${context.packageName}_preferences", Context.MODE_PRIVATE)
        if (!prefs.contains("pointerCapture")) {
            prefs.edit()
                .putBoolean("pointerCapture", false)
                .putBoolean("showMouseHelper", true)
                .putBoolean("fullscreen", true)
                .apply()
        }
    }

    private fun fetchText(urlString: String): String {
        val conn = (URL(urlString).openConnection() as HttpURLConnection).apply {
            connectTimeout = 15_000
            readTimeout = 20_000
            instanceFollowRedirects = true
        }
        return conn.inputStream.bufferedReader().use { it.readText() }
    }

    private fun downloadFile(urlString: String, dest: File, onBytes: (Long, Long) -> Unit) {
        val conn = (URL(urlString).openConnection() as HttpURLConnection).apply {
            connectTimeout = 20_000
            readTimeout = 60_000
            instanceFollowRedirects = true
        }
        val total = conn.contentLengthLong
        var downloaded = 0L
        val buffer = ByteArray(64 * 1024)
        BufferedInputStream(conn.inputStream).use { input ->
            FileOutputStream(dest).use { output ->
                while (true) {
                    val read = input.read(buffer)
                    if (read <= 0) break
                    output.write(buffer, 0, read)
                    downloaded += read
                    onBytes(downloaded, total)
                }
            }
        }
    }

    private fun extractTarXz(archive: File, destDir: File) {
        val dirModes = mutableListOf<Pair<File, Int>>()
        val deferredLinks = mutableListOf<Pair<File, String>>()

        XZInputStream(BufferedInputStream(archive.inputStream())).use { xz ->
            TarArchiveInputStream(xz).use { tar ->
                var entry: TarArchiveEntry? = tar.nextEntry
                val buf = ByteArray(64 * 1024)
                while (entry != null) {
                    val cleanName = entry.name.removePrefix("./").trimStart('/')
                    if (cleanName.isNotEmpty() && !cleanName.startsWith("dev/") && cleanName != "dev") {
                        val outFile = File(destDir, cleanName)
                        if (!outFile.canonicalPath.startsWith(destDir.canonicalPath)) {
                            throw SecurityException("Blocked path traversal entry: ${entry.name}")
                        }
                        when {
                            entry.isDirectory -> {
                                outFile.mkdirs()
                                Os.chmod(outFile.absolutePath, 0b111_101_101)
                                dirModes.add(outFile to (entry.mode and 0b111_111_111))
                            }
                            entry.isSymbolicLink -> {
                                outFile.parentFile?.mkdirs()
                                outFile.delete()
                                Os.symlink(entry.linkName, outFile.absolutePath)
                            }
                            entry.isLink -> {
                                outFile.parentFile?.mkdirs()
                                deferredLinks.add(outFile to entry.linkName.removePrefix("./").trimStart('/'))
                            }
                            entry.isFile -> {
                                outFile.parentFile?.mkdirs()
                                outFile.delete()
                                FileOutputStream(outFile).use { out ->
                                    while (true) {
                                        val n = tar.read(buf)
                                        if (n <= 0) break
                                        out.write(buf, 0, n)
                                    }
                                }
                                Os.chmod(outFile.absolutePath, entry.mode and 0b111_111_111)
                            }
                        }
                    }
                    entry = tar.nextEntry
                }
            }
        }

        for ((linkFile, targetRel) in deferredLinks) {
            val targetFile = File(destDir, targetRel)
            if (targetFile.exists()) {
                linkFile.delete()
                Os.link(targetFile.absolutePath, linkFile.absolutePath)
            }
        }
        for ((dir, mode) in dirModes.asReversed()) {
            try {
                Os.chmod(dir.absolutePath, mode or 0b111_000_000)
            } catch (_: Exception) {
            }
        }
    }
}
