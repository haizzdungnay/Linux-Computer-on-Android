package dev.local.linuxdesktop.launcher

/** Resolves the latest Debian 13 (trixie) arm64 rootfs tarball URL from LXC image index. */
object RootfsCatalog {
    const val INDEX_URL = "https://images.linuxcontainers.org/images/debian/trixie/arm64/default/"
    private val BUILD_DIR_REGEX = Regex("""href="(\d{8}_\d{2}(?::|%3A)\d{2}/)"""")

    fun latestTrixieRootfsUrl(indexHtml: String, baseUrl: String = INDEX_URL): String {
        val latestDir = BUILD_DIR_REGEX.findAll(indexHtml)
            .map { it.groupValues[1] }
            .maxOrNull()
            ?: throw IllegalStateException("No Debian trixie arm64 build found in index")
        val normalizedBase = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
        return "${normalizedBase}${latestDir}rootfs.tar.xz"
    }
}
