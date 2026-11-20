package dev.local.linuxdesktop.launcher

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

private const val RUN_PERMISSION = "com.termux.permission.RUN_COMMAND"
private const val PERMISSION_REQUEST = 7
private const val RETRY_DELAY_MS = 1500L

class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var check: Button
    private lateinit var start: Button
    private lateinit var stop: Button
    private lateinit var resume: Button
    private val handler = Handler(Looper.getMainLooper())
    private val retry = Runnable { execute(Command.STATUS) }
    private var visible = false
    private var uiError: String? = null
    private var permissionAsked = false
    private var launchPending = true
    private lateinit var flow: LaunchFlow

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val prefs = getPreferences(MODE_PRIVATE)
        flow = LaunchFlow(prefs.getBoolean("startIssued", false))
        launchPending = savedInstanceState?.getBoolean("launchPending") ?: true
        permissionAsked = savedInstanceState?.getBoolean("permissionAsked") ?: false
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(32, 48, 32, 32)
        }
        status = TextView(this).apply { textSize = 18f; setTextIsSelectable(true) }
        layout.addView(status)
        fun button(label: String, action: () -> Unit): Button = Button(this).also {
            it.text = label
            it.setOnClickListener { action() }
            layout.addView(it)
        }
        check = button("Check status") { execute(Command.STATUS) }
        start = button("Start") {
            launchPending = true
            flow = LaunchFlow()
            issueStart()
        }
        stop = button("Stop") {
            launchPending = false
            handler.removeCallbacks(retry)
            execute(Command.STOP)
        }
        resume = button("Resume desktop") {
            launchPending = true
            flow = LaunchFlow(startIssued = true)
            execute(Command.STATUS)
        }
        button("App permissions") {
            try {
                startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:$packageName")))
            } catch (e: Exception) {
                uiError = "Cannot open app settings: ${e.message}"
                render()
            }
        }
        setContentView(layout)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        launchPending = true
        flow = LaunchFlow(getPreferences(MODE_PRIVATE).getBoolean("startIssued", false))
    }

    override fun onSaveInstanceState(outState: Bundle) {
        outState.putBoolean("launchPending", launchPending)
        outState.putBoolean("permissionAsked", permissionAsked)
        super.onSaveInstanceState(outState)
    }

    override fun onResume() {
        super.onResume()
        visible = true
        TermuxCommands.listener = { completed ->
            if (completed == Command.STOP && TermuxCommands.state == DesktopState.STOPPED) {
                flow.startIssued = getPreferences(MODE_PRIVATE).getBoolean("startIssued", false)
            }
            render()
            if (completed != null && launchPending) reconcile(completed)
        }
        render()
        if (checkSelfPermission(RUN_PERMISSION) != PackageManager.PERMISSION_GRANTED) {
            if (!permissionAsked) {
                permissionAsked = true
                requestPermissions(arrayOf(RUN_PERMISSION), PERMISSION_REQUEST)
            }
        } else if (!TermuxCommands.busy) {
            flow.startIssued = getPreferences(MODE_PRIVATE).getBoolean("startIssued", false)
            execute(Command.STATUS)
        }
    }

    override fun onPause() {
        visible = false
        handler.removeCallbacks(retry)
        TermuxCommands.listener = null
        super.onPause()
    }

    private fun reconcile(completed: Command) {
        when (flow.result(completed, TermuxCommands.state, visible)) {
            LaunchAction.OPEN -> {
                launchPending = false
                if (openDesktop()) {
                    getPreferences(MODE_PRIVATE).edit().putBoolean("startIssued", false).apply()
                    flow.startIssued = false
                }
            }
            LaunchAction.RETRY -> if (visible) handler.postDelayed(retry, RETRY_DELAY_MS)
            LaunchAction.NONE -> {
                if (TermuxCommands.state == DesktopState.STOPPED && flow.startIssued) {
                    launchPending = false
                    uiError = "Desktop is stopped. Check status or start manually."
                    render()
                }
            }
        }
    }

    private fun issueStart() {
        if (TermuxCommands.busy || checkSelfPermission(RUN_PERMISSION) != PackageManager.PERMISSION_GRANTED) {
            launchPending = false
            uiError = "Start not sent. Check permission and command status."
            render()
            return
        }
        if (!getPreferences(MODE_PRIVATE).edit().putBoolean("startIssued", true).commit()) {
            uiError = "Cannot record start request. Start cancelled."
            render()
            return
        }
        flow.startIssued = true
        execute(Command.START)
    }

    private fun execute(command: Command) {
        uiError = null
        if (checkSelfPermission(RUN_PERMISSION) != PackageManager.PERMISSION_GRANTED) {
            uiError = "Termux RUN_COMMAND permission required. Grant it in app permissions; enable allow-external-apps in Termux."
            render()
            if (!permissionAsked) {
                permissionAsked = true
                requestPermissions(arrayOf(RUN_PERMISSION), PERMISSION_REQUEST)
            }
            return
        }
        TermuxCommands.run(applicationContext, command)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != PERMISSION_REQUEST) return
        if (grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED) {
            if (visible && !TermuxCommands.busy) execute(Command.STATUS)
        } else {
            launchPending = false
            uiError = "Termux permission denied. Grant Run commands in Termux environment under app permissions."
            render()
        }
    }

    private fun openDesktop(): Boolean {
        if (!visible || TermuxCommands.busy || TermuxCommands.state != DesktopState.RUNNING) return false
        return try {
            val intent = packageManager.getLaunchIntentForPackage("com.termux.x11")
                ?: throw IllegalStateException("Termux:X11 is not installed or has no launch activity")
            startActivity(intent)
            true
        } catch (e: Exception) {
            uiError = "Cannot open Termux:X11: ${e.message}"
            render()
            false
        }
    }

    private fun render() {
        status.text = uiError ?: TermuxCommands.message
        val idle = !TermuxCommands.busy
        check.isEnabled = idle
        start.isEnabled = idle && TermuxCommands.state == DesktopState.STOPPED
        stop.isEnabled = idle && TermuxCommands.state != DesktopState.STOPPED
        resume.isEnabled = idle && TermuxCommands.state == DesktopState.RUNNING
    }
}
