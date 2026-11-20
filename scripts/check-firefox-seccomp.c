/* AArch64: browser SIGSYS must arrive; an errno filter must still deny access. */
#define _GNU_SOURCE
#include <errno.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <signal.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <ucontext.h>
#include <unistd.h>

static volatile sig_atomic_t trapped;

static void trap(int signal_number, siginfo_t *info, void *context) {
    if (signal_number == SIGSYS && info->si_errno == 42) {
        ((ucontext_t *)context)->uc_mcontext.regs[0] = 4242;
        trapped++;
    }
}

int main(void) {
    struct sigaction action = {.sa_sigaction = trap, .sa_flags = SA_SIGINFO};
    sigemptyset(&action.sa_mask);
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_getppid, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_TRAP | 42),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_getpgid, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EACCES),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog program = {.len = sizeof(filter) / sizeof(filter[0]), .filter = filter};
    if (sigaction(SIGSYS, &action, NULL) || prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) ||
        prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &program)) {
        perror("seccomp setup");
        return 2;
    }
    long handled = syscall(SYS_getppid);
    errno = 0;
    long denied = syscall(SYS_getpgid, 0);
    int denial_errno = errno;
    printf("handler=%d result=%ld denied=%ld errno=%d seccomp=%d\n",
           trapped, handled, denied, denial_errno, prctl(PR_GET_SECCOMP));
    return !(trapped == 1 && handled == 4242 && denied == -1 && denial_errno == EACCES);
}
