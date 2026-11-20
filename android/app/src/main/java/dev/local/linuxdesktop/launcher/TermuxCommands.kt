package dev.local.linuxdesktop.launcher

import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Handler
import android.os.Looper
import java.util.UUID

private const val HOME = "/data/data/com.termux/files/home"
private const val SCRIPTS = "$HOME/.local/linux-desktop"
private const val TIMEOUT_MS = 60000L

enum class Command(val path: String) {
    START("$SCRIPTS/start-linux.sh"), STOP("$SCRIPTS/stop-linux.sh"), STATUS("$SCRIPTS/status-linux.sh")
}

object TermuxCommands {
    private val handler = Handler(Looper.getMainLooper())
    private var activeId: String? = null
    private var activeCommand: Command? = null
    private var appContext: Context? = null
    var state = DesktopState.UNKNOWN
        private set
    var message = "Status unknown. Check status before starting or stopping."
        private set
    var busy = false
        private set
    var listener: ((Command?) -> Unit)? = null

    fun run(context: Context, command: Command) {
        if (busy) return
        appContext = context.applicationContext
        val id = UUID.randomUUID().toString()
        activeId = id
        activeCommand = command
        busy = true
        state = DesktopState.UNKNOWN
        message = "Running ${command.name.lowercase()}…"
        listener?.invoke(null)
        var callback: PendingIntent? = null
        try {
            val resultIntent = Intent(context, ResultReceiver::class.java).setData(Uri.parse("linuxdesktop://result/$id"))
            val pending = PendingIntent.getBroadcast(context, 0, resultIntent,
                PendingIntent.FLAG_ONE_SHOT or if (Build.VERSION.SDK_INT >= 31) PendingIntent.FLAG_MUTABLE else 0)
            callback = pending
            val intent = Intent("com.termux.RUN_COMMAND").setClassName("com.termux", "com.termux.app.RunCommandService")
                .putExtra("com.termux.RUN_COMMAND_PATH", command.path)
                .putExtra("com.termux.RUN_COMMAND_WORKDIR", HOME)
                .putExtra("com.termux.RUN_COMMAND_BACKGROUND", true)
                .putExtra("com.termux.RUN_COMMAND_PENDING_INTENT", pending)
            if (context.startService(intent) == null) throw IllegalStateException("Termux service unavailable")
            handler.postDelayed({
                if (activeId == id) {
                    pending.cancel()
                    finish(DesktopState.UNKNOWN, "Command timed out; outcome unknown. Check status before retrying.")
                }
            }, TIMEOUT_MS)
        } catch (e: Exception) {
            callback?.cancel()
            finish(DesktopState.UNKNOWN, "Could not start Termux command: ${e.message}. Check permission and Termux setup.")
        }
    }

    fun receive(intent: Intent) {
        if (intent.data?.lastPathSegment != activeId || activeId == null) return
        try {
            val result = intent.getBundleExtra("result")
            val err = if (result?.containsKey("err") == true) result.getInt("err") else null
            val exit = if (result?.containsKey("exitCode") == true) result.getInt("exitCode") else null
            val stdout = result?.getString("stdout")
            val outcome = parseResult(err, exit, stdout)
            val detail = result?.getString("errmsg").orEmpty().ifBlank { result?.getString("stderr").orEmpty() }
            val msg = if (outcome == DesktopState.UNKNOWN) {
                "Command failed or returned an invalid status (err=$err, exit=$exit). ${detail.take(1000)} Check status before retrying."
            } else "Desktop ${outcome.name.lowercase()}."
            finish(outcome, msg)
        } catch (e: Exception) {
            finish(DesktopState.UNKNOWN, "Invalid Termux callback: ${e.message}. Check status before retrying.")
        }
    }

    private fun finish(outcome: DesktopState, text: String) {
        val completedCommand = activeCommand
        if (completedCommand != null) {
            val prefs = appContext?.getSharedPreferences("${MainActivity::class.java.simpleName}", Context.MODE_PRIVATE)
            if (prefs != null) {
                val current = prefs.getBoolean("startIssued", false)
                val updated = startIssuedAfterResult(current, completedCommand, outcome)
                if (current != updated) prefs.edit().putBoolean("startIssued", updated).apply()
            }
        }
        activeCommand = null
        activeId = null
        busy = false
        state = outcome
        message = text
        listener?.invoke(completedCommand)
    }
}

class ResultReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) = TermuxCommands.receive(intent)
}
