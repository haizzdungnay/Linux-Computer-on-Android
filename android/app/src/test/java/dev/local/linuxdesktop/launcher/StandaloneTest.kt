package dev.local.linuxdesktop.launcher

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class StandaloneTest {
    @Test
    fun latestTrixieRootfsUrlPicksNewestTimestamp() {
        val sampleHtml = """
            <a href="../">../</a>
            <a href="20261116_22%3A14/">20261116_22:14/</a>
            <a href="20261118_05%3A24/">20261118_05:24/</a>
            <a href="20261117_05%3A24/">20261117_05:24/</a>
        """.trimIndent()
        val url = RootfsCatalog.latestTrixieRootfsUrl(sampleHtml)
        assertEquals(
            "https://images.linuxcontainers.org/images/debian/trixie/arm64/default/20261118_05%3A24/rootfs.tar.xz",
            url
        )
    }

    @Test(expected = IllegalStateException::class)
    fun latestTrixieRootfsUrlRejectsEmptyIndex() {
        RootfsCatalog.latestTrixieRootfsUrl("<html><body>empty</body></html>")
    }

    @Test
    fun prootCommandBuilderSetsIsolatedPathsAndLoader() {
        val nativeDir = File("/data/app/dev.local.linuxdesktop.launcher/lib/arm64")
        val libDir = File("/data/user/0/dev.local.linuxdesktop.launcher/files/linux-desktop/lib")
        val tmpDir = File("/data/user/0/dev.local.linuxdesktop.launcher/files/linux-desktop/tmp")
        val rootfs = File("/data/user/0/dev.local.linuxdesktop.launcher/files/linux-desktop/debian/rootfs")
        val proot = File(nativeDir, "libproot.so")

        val args = ProotCommandBuilder.buildArgs(proot, rootfs, tmpDir, "echo ok")
        assertEquals(proot.absolutePath, args.first())
        assertTrue(args.contains("${tmpDir.absolutePath}:/tmp"))
        assertTrue(args.contains("DISPLAY=:2"))
        assertEquals("echo ok", args.last())

        val env = ProotCommandBuilder.buildEnv(nativeDir, libDir, tmpDir)
        assertEquals(File(nativeDir, "libproot-loader.so").absolutePath, env["PROOT_LOADER"])
        assertEquals(tmpDir.absolutePath, env["PROOT_TMP_DIR"])
        assertTrue(env["LD_LIBRARY_PATH"]!!.contains(libDir.absolutePath))
    }
}
