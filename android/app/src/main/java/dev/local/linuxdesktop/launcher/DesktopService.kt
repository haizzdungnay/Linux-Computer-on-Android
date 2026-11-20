package dev.local.linuxdesktop.launcher

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import java.io.BufferedReader
import java.io.InputStreamReader
import java.util.concurrent.atomic.AtomicBoolean

/** Manages the embedded X11 server + Debian PRoot XFCE session lifecycle. */
class DesktopService : Service() {
    companion object {
        const val ACTION_START = "dev.local.linuxdesktop.launcher.ACTION_START_DESKTOP"
        const val ACTION_STOP = "dev.local.linuxdesktop.launcher.ACTION_STOP_DESKTOP"
        private const val CHANNEL_ID = "linux_desktop_session"
        private const val NOTIFICATION_ID = 4102

        @Volatile
        var running: Boolean = false
            private set
    }

    inner class LocalBinder : Binder() {
        fun service(): DesktopService = this@DesktopService
    }

    private val binder = LocalBinder()
    private val stopping = AtomicBoolean(false)
    @Volatile
    private var prootProcess: Process? = null
    private var workerThread: Thread? = null

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> stopDesktop()
            ACTION_START, null -> startDesktop()
        }
        return START_NOT_STICKY
    }

    @Synchronized
    fun startDesktop() {
        if (running && prootProcess?.isAlive == true) {
            openX11Viewer()
            return
        }
        stopping.set(false)
        ensureNotification()
        running = true

        val paths = StandalonePaths(this)
        paths.ensureDirs()
        paths.x11Socket.delete()

        startForegroundService(Intent(this, X11ServerService::class.java))

        workerThread = Thread({
            try {
                waitForSocket(paths)
                val runner = ProotRunner(this, paths)
                val proc = runner.startProcess(
                    "exec /bin/sh /root/.local/share/linux-desktop/tablet-session.sh :2 /root/.ld-test/xfce-config ''"
                )
                prootProcess = proc
                paths.sessionLog.writeText("Started PRoot XFCE session on :2\n")
                openX11Viewer()

                BufferedReader(InputStreamReader(proc.inputStream)).use { reader ->
                    while (true) {
                        val line = reader.readLine() ?: break
                        paths.sessionLog.appendText("$line\n")
                    }
                }
                val code = proc.waitFor()
                paths.sessionLog.appendText("Session exited with code $code\n")
            } catch (e: Exception) {
                paths.sessionLog.appendText("DesktopService error: ${e.message}\n")
            } finally {
                running = false
                prootProcess = null
                if (!stopping.get()) {
                    stopService(Intent(this, X11ServerService::class.java))
                }
                stopSelf()
            }
        }, "linux-desktop-session").apply { start() }
    }

    @Synchronized
    fun stopDesktop() {
        stopping.set(true)
        prootProcess?.destroyForcibly()
        prootProcess = null
        running = false
        stopService(Intent(this, X11ServerService::class.java))
        sendBroadcast(Intent(com.termux.x11.MainActivity.ACTION_STOP).setPackage(packageName))
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun waitForSocket(paths: StandalonePaths) {
        val deadline = System.currentTimeMillis() + 12_000L
        while (System.currentTimeMillis() < deadline) {
            if (paths.x11Socket.exists()) return
            Thread.sleep(150)
        }
        throw IllegalStateException("Timed out waiting for embedded X11 socket at ${paths.x11Socket.absolutePath}")
    }

    private fun openX11Viewer() {
        val intent = Intent(this, com.termux.x11.MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
        }
        startActivity(intent)
    }

    private fun ensureNotification() {
        val mgr = getSystemService(NotificationManager::class.java)
        mgr.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "Linux Desktop Session", NotificationManager.IMPORTANCE_LOW)
        )
        val notification = Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("Linux Desktop")
            .setContentText("Debian 13 XFCE running on :2")
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setOngoing(true)
            .build()
        startForeground(NOTIFICATION_ID, notification)
    }
}
