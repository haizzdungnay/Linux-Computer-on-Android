package dev.local.linuxdesktop.launcher

enum class DesktopState { RUNNING, STOPPED, UNKNOWN }

enum class LaunchAction { NONE, OPEN, RETRY }

fun startIssuedAfterResult(startIssued: Boolean, command: Command, state: DesktopState): Boolean =
    startIssued && !(command == Command.STOP && state == DesktopState.STOPPED)

class LaunchFlow(var startIssued: Boolean = false) {
    private var retries = 0

    fun result(command: Command, state: DesktopState, visible: Boolean): LaunchAction {
        startIssued = startIssuedAfterResult(startIssued, command, state)
        if (command == Command.STOP && state == DesktopState.STOPPED) return LaunchAction.NONE
        if (state == DesktopState.UNKNOWN) {
            return if (retries++ < 2) LaunchAction.RETRY else LaunchAction.NONE
        }
        if (state == DesktopState.RUNNING) return if (visible) LaunchAction.OPEN else LaunchAction.NONE
        return LaunchAction.NONE
    }
}

fun parseResult(err: Int?, exitCode: Int?, stdout: String?): DesktopState {
    if (err != -1 || exitCode != 0) return DesktopState.UNKNOWN
    return when (stdout) {
        "RUNNING", "RUNNING\n" -> DesktopState.RUNNING
        "STOPPED", "STOPPED\n" -> DesktopState.STOPPED
        else -> DesktopState.UNKNOWN
    }
}
