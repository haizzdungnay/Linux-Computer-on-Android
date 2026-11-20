package dev.local.linuxdesktop.launcher

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView

/** Standalone auto-installer & launcher for Debian 13 + XFCE + WhiteSur on Android. */
class MainActivity : Activity() {
    private lateinit var installer: RootfsInstaller
    private lateinit var paths: StandalonePaths
    private lateinit var statusView: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var logView: TextView
    private lateinit var logScroll: ScrollView
    private lateinit var installBtn: Button
    private lateinit var startBtn: Button
    private lateinit var stopBtn: Button
    private lateinit var settingsBtn: Button

    @Volatile
    private var installing = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        installer = RootfsInstaller(this)
        paths = StandalonePaths(this)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(36, 48, 36, 36)
        }

        val title = TextView(this).apply {
            text = "Linux Computer on Android"
            textSize = 22f
            setPadding(0, 0, 0, 12)
        }
        statusView = TextView(this).apply {
            textSize = 16f
            setTextIsSelectable(true)
            setPadding(0, 0, 0, 16)
        }
        progressBar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = 100
            visibility = View.GONE
        }

        fun addButton(label: String, onClick: () -> Unit): Button = Button(this).also {
            it.text = label
            it.setOnClickListener { onClick() }
            root.addView(it, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ))
        }

        root.addView(title)
        root.addView(statusView)
        root.addView(progressBar, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ))

        installBtn = addButton("Install Linux Desktop") { beginInstall() }
        startBtn = addButton("Start & Open Desktop") { launchDesktop() }
        stopBtn = addButton("Stop Desktop") { stopDesktop() }
        settingsBtn = addButton("X11 Display Settings") {
            startActivity(Intent(this, com.termux.x11.LoriePreferences::class.java))
        }

        logView = TextView(this).apply {
            textSize = 12f
            typeface = android.graphics.Typeface.MONOSPACE
            setTextIsSelectable(true)
            setPadding(16, 16, 16, 16)
        }
        logScroll = ScrollView(this).apply { addView(logView) }
        root.addView(logScroll, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f
        ))

        setContentView(root)
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 101)
        }
    }

    override fun onResume() {
        super.onResume()
        refreshUi()
    }

    private fun refreshUi() {
        val installed = installer.isInstalled()
        val running = DesktopService.running
        statusView.text = when {
            installing -> "Installing Debian 13 + XFCE + WhiteSur..."
            running -> "Status: Running on embedded X11 (:2)"
            installed -> "Status: Debian 13 XFCE installed (Stopped)"
            else -> "Status: Not installed yet (No Termux required)"
        }
        installBtn.text = if (installed) "Reinstall / Repair Desktop" else "Install Linux Desktop"
        installBtn.isEnabled = !installing && !running
        startBtn.isEnabled = installed && !installing
        startBtn.text = if (running) "Open Desktop" else "Start & Open Desktop"
        stopBtn.isEnabled = running && !installing
        progressBar.visibility = if (installing) View.VISIBLE else View.GONE
    }

    private fun beginInstall() {
        if (installing) return
        installing = true
        logView.text = ""
        progressBar.progress = 0
        refreshUi()

        Thread({
            try {
                installer.install(
                    onProgress = { p ->
                        runOnUiThread {
                            progressBar.progress = p.percent
                            statusView.text = "${p.step} (${p.percent}%) ${p.detail}"
                        }
                    },
                    onLog = { line ->
                        runOnUiThread {
                            logView.append("$line\n")
                            logScroll.post { logScroll.fullScroll(View.FOCUS_DOWN) }
                        }
                    }
                )
            } catch (e: Exception) {
                runOnUiThread {
                    logView.append("\nERROR: ${e.message}\n")
                    statusView.text = "Installation failed: ${e.message}"
                }
            } finally {
                runOnUiThread {
                    installing = false
                    refreshUi()
                }
            }
        }, "linux-desktop-installer").start()
    }

    private fun launchDesktop() {
        if (!installer.isInstalled()) return
        if (DesktopService.running) {
            startActivity(Intent(this, com.termux.x11.MainActivity::class.java))
            return
        }
        startForegroundService(Intent(this, DesktopService::class.java).setAction(DesktopService.ACTION_START))
        statusView.postDelayed({ refreshUi() }, 500)
    }

    private fun stopDesktop() {
        startService(Intent(this, DesktopService::class.java).setAction(DesktopService.ACTION_STOP))
        statusView.postDelayed({ refreshUi() }, 300)
    }
}
