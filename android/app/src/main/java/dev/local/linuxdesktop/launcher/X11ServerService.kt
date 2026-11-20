package dev.local.linuxdesktop.launcher

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.system.Os
import com.termux.x11.CmdEntryPoint

/** Hosts the embedded Lorie X11 server in a dedicated :x11 process. */
class X11ServerService : Service() {
    companion object {
        const val ACTION_STOP = "dev.local.linuxdesktop.launcher.ACTION_STOP_X11"
        private const val CHANNEL_ID = "linux_desktop_x11"
        private const val NOTIFICATION_ID = 4101
    }

    private var entryPoint: CmdEntryPoint? = null

    override fun onCreate() {
        super.onCreate()
        val paths = StandalonePaths(this)
        paths.ensureDirs()

        Os.setenv("TMPDIR", paths.tmpDir.absolutePath, true)
        if (paths.debianXkbDir.isDirectory) {
            Os.setenv("XKB_CONFIG_ROOT", paths.debianXkbDir.absolutePath, true)
        }

        ensureNotification()
        if (entryPoint == null) {
            entryPoint = CmdEntryPoint.createInApp(this, arrayOf(":2"))
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stopSelf()
            return START_NOT_STICKY
        }
        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        android.os.Process.killProcess(android.os.Process.myPid())
    }

    override fun onBind(intent: Intent?): IBinder? = entryPoint

    private fun ensureNotification() {
        val mgr = getSystemService(NotificationManager::class.java)
        mgr.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "X11 Display Server", NotificationManager.IMPORTANCE_LOW)
        )
        val notification = android.app.Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("Linux Desktop Display")
            .setContentText("Embedded X11 server active on :2")
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .setOngoing(true)
            .build()
        startForeground(NOTIFICATION_ID, notification)
    }
}
