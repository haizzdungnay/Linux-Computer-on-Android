package dev.local.linuxdesktop.launcher

import org.junit.Assert.assertEquals
import org.junit.Test

class CommandResultTest {
    @Test fun launchRequiresForegroundAndVerifiedRunning() {
        assertEquals(LaunchAction.OPEN, LaunchFlow(true).result(Command.START, DesktopState.RUNNING, true))
        assertEquals(LaunchAction.NONE, LaunchFlow(true).result(Command.START, DesktopState.RUNNING, false))
        assertEquals(LaunchAction.RETRY, LaunchFlow(true).result(Command.START, DesktopState.UNKNOWN, true))
        assertEquals(LaunchAction.NONE, LaunchFlow(true).result(Command.START, DesktopState.STOPPED, true))
        assertEquals(LaunchAction.OPEN, LaunchFlow().result(Command.STATUS, DesktopState.RUNNING, true))
        assertEquals(LaunchAction.NONE, LaunchFlow().result(Command.STATUS, DesktopState.RUNNING, false))
    }

    @Test fun exportedActivityStatusNeverStartsWithoutUserPress() {
        val flow = LaunchFlow()
        assertEquals(LaunchAction.NONE, flow.result(Command.STATUS, DesktopState.STOPPED, true))
    }

    @Test fun alreadyRunningOpensOnlyWhenResumed() {
        val flow = LaunchFlow()
        assertEquals(LaunchAction.NONE, flow.result(Command.STATUS, DesktopState.RUNNING, false))
        assertEquals(LaunchAction.OPEN, flow.result(Command.STATUS, DesktopState.RUNNING, true))
    }

    @Test fun lostStartCallbackDoesNotRepeatMutationAfterRecreation() {
        val flow = LaunchFlow(startIssued = true)
        assertEquals(LaunchAction.NONE, flow.result(Command.STATUS, DesktopState.STOPPED, true))
    }

    @Test fun unknownStartReconcilesWithoutRepeatingStart() {
        val flow = LaunchFlow(startIssued = true)
        assertEquals(LaunchAction.RETRY, flow.result(Command.START, DesktopState.UNKNOWN, true))
        assertEquals(LaunchAction.NONE, flow.result(Command.STATUS, DesktopState.STOPPED, true))
    }

    @Test fun stoppedStatusDoesNotStartOnResume() {
        val flow = LaunchFlow()
        assertEquals(LaunchAction.NONE, flow.result(Command.STATUS, DesktopState.STOPPED, false))
        assertEquals(LaunchAction.NONE, flow.result(Command.STATUS, DesktopState.STOPPED, true))
    }

    @Test fun confirmedStopClearsStartMarkerEvenWhilePaused() {
        val flow = LaunchFlow(startIssued = true)
        assertEquals(LaunchAction.NONE, flow.result(Command.STOP, DesktopState.STOPPED, false))
        assertEquals(false, flow.startIssued)
        assertEquals(LaunchAction.NONE, flow.result(Command.STATUS, DesktopState.STOPPED, true))
    }

    @Test fun ambiguousStopDoesNotClearStartMarker() {
        val flow = LaunchFlow(startIssued = true)
        assertEquals(LaunchAction.RETRY, flow.result(Command.STOP, DesktopState.UNKNOWN, false))
        assertEquals(true, flow.startIssued)
        assertEquals(LaunchAction.NONE, flow.result(Command.STATUS, DesktopState.STOPPED, true))
    }

    @Test fun unknownStatusesRetryOnlyTwice() {
        val flow = LaunchFlow()
        assertEquals(LaunchAction.RETRY, flow.result(Command.STATUS, DesktopState.UNKNOWN, true))
        assertEquals(LaunchAction.RETRY, flow.result(Command.STATUS, DesktopState.UNKNOWN, true))
        assertEquals(LaunchAction.NONE, flow.result(Command.STATUS, DesktopState.UNKNOWN, true))
    }

    @Test fun successRequiresExactStatusAndBothCodes() {
        assertEquals(DesktopState.RUNNING, parseResult(-1, 0, "RUNNING\n"))
        assertEquals(DesktopState.STOPPED, parseResult(-1, 0, "STOPPED\n"))
        assertEquals(DesktopState.UNKNOWN, parseResult(0, 0, "RUNNING\n"))
        assertEquals(DesktopState.UNKNOWN, parseResult(-1, 1, "RUNNING\n"))
        assertEquals(DesktopState.UNKNOWN, parseResult(null, 0, "RUNNING\n"))
        assertEquals(DesktopState.UNKNOWN, parseResult(-1, null, "RUNNING\n"))
        assertEquals(DesktopState.UNKNOWN, parseResult(-1, 0, "RUNNING\nSTOPPED\n"))
        for (status in listOf("BUSY", "UNKNOWN", "ERROR", "STARTING", "STOPPING", "FAILED")) {
            assertEquals(DesktopState.UNKNOWN, parseResult(-1, 0, "$status\n"))
        }
        assertEquals(DesktopState.UNKNOWN, parseResult(-1, 0, null))
    }
}
