package dev.local.linuxdesktop.launcher

import android.content.Context
import android.system.Os
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader

/** Executes commands inside the embedded Debian PRoot container. */
class ProotRunner(private val context: Context, val paths: StandalonePaths = StandalonePaths(context)) {

    fun prepareHostRuntime() {
        paths.ensureDirs()
        if (!paths.tallocLib.isFile || paths.tallocLib.length() == 0L) {
            context.assets.open("native/arm64-v8a/libtalloc.so.2").use { input ->
                paths.tallocLib.outputStream().use { output -> input.copyTo(output) }
            }
        }
        Os.chmod(paths.tallocLib.absolutePath, 0b111_101_101)
    }

    fun startProcess(guestCommand: String): Process {
        prepareHostRuntime()
        val prootBin = File(paths.nativeLibDir, "libproot.so")
        require(prootBin.isFile) { "Missing PRoot binary at ${prootBin.absolutePath}" }

        val args = ProotCommandBuilder.buildArgs(prootBin, paths.rootfsDir, paths.tmpDir, guestCommand)
        val envMap = ProotCommandBuilder.buildEnv(paths.nativeLibDir, paths.libDir, paths.tmpDir)
        val builder = ProcessBuilder(args).redirectErrorStream(true)
        builder.environment().putAll(envMap)
        return builder.start()
    }

    fun runAndStream(guestCommand: String, onLine: (String) -> Unit): Int {
        val process = startProcess(guestCommand)
        BufferedReader(InputStreamReader(process.inputStream)).use { reader ->
            while (true) {
                val line = reader.readLine() ?: break
                onLine(line)
            }
        }
        return process.waitFor()
    }
}
