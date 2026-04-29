/* SPDX-License-Identifier: MIT
 *
 * ei_inject — minimal libei client that injects pointer + button + key events
 * into a gamescope EIS server (gamescope-0-ei) without affecting the host
 * cursor or keyboard.
 *
 * Reads newline-delimited commands from stdin and emits ei events:
 *   move <x> <y>     — absolute pointer position in gamescope surface coords
 *   click <btn>      — press+release; btn = 1 (left), 2 (middle), 3 (right)
 *   down <btn>
 *   up <btn>
 *   key <code>       — press+release linux input keycode (e.g. 1=ESC)
 *   keydown <code>
 *   keyup <code>
 *   sleep <ms>
 *   bye              — disconnect cleanly
 *
 * Connect via env: LIBEI_SOCKET=gamescope-0-ei (gamescope sets this in
 *   $XDG_RUNTIME_DIR). Run as: LIBEI_SOCKET=gamescope-0-ei ./ei_inject
 */
#include <assert.h>
#include <errno.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <linux/input-event-codes.h>

#include <libei.h>

static struct ei *ei_ctx;
static struct ei_device *ptr_abs;     /* EI_DEVICE_CAP_POINTER_ABSOLUTE */
static struct ei_device *ptr_btn;     /* device with EI_DEVICE_CAP_BUTTON */
static struct ei_device *kbd;
static struct ei_seat *default_seat;
static int have_abs = 0, have_btn = 0, have_kbd = 0;
static uint32_t sequence = 0;
static int verbose = 0;

#define LOG(...) do { if (verbose) { fprintf(stderr, "[ei] " __VA_ARGS__); fflush(stderr); } } while(0)

static int btn_code(int n) {
    switch (n) {
        case 1: return BTN_LEFT;
        case 2: return BTN_MIDDLE;
        case 3: return BTN_RIGHT;
        default: return BTN_LEFT;
    }
}

static void pump_events(int timeout_ms) {
    struct pollfd pfd = { .fd = ei_get_fd(ei_ctx), .events = POLLIN };
    int rc = poll(&pfd, 1, timeout_ms);
    if (rc <= 0) return;
    ei_dispatch(ei_ctx);
    struct ei_event *e;
    while ((e = ei_get_event(ei_ctx)) != NULL) {
        enum ei_event_type type = ei_event_get_type(e);
        switch (type) {
        case EI_EVENT_CONNECT:
            LOG("connected\n"); break;
        case EI_EVENT_DISCONNECT:
            LOG("disconnected\n"); break;
        case EI_EVENT_SEAT_ADDED:
            if (!default_seat) {
                default_seat = ei_seat_ref(ei_event_get_seat(e));
                LOG("seat: %s\n", ei_seat_get_name(default_seat));
                ei_seat_bind_capabilities(default_seat,
                    EI_DEVICE_CAP_POINTER_ABSOLUTE,
                    EI_DEVICE_CAP_BUTTON,
                    EI_DEVICE_CAP_SCROLL,
                    EI_DEVICE_CAP_KEYBOARD,
                    NULL);
            }
            break;
        case EI_EVENT_DEVICE_ADDED: {
            struct ei_device *d = ei_event_get_device(e);
            if (ei_device_has_capability(d, EI_DEVICE_CAP_POINTER_ABSOLUTE) && !ptr_abs) {
                ptr_abs = ei_device_ref(d);
                LOG("abs ptr device: %s w=%u h=%u\n",
                    ei_device_get_name(d),
                    ei_device_get_width(d), ei_device_get_height(d));
                uint32_t i = 0; struct ei_region *r;
                while ((r = ei_device_get_region(d, i++)) != NULL) {
                    LOG("  region %u: %dx%d @%d,%d\n", i-1,
                        ei_region_get_width(r), ei_region_get_height(r),
                        ei_region_get_x(r), ei_region_get_y(r));
                }
            }
            if (ei_device_has_capability(d, EI_DEVICE_CAP_BUTTON) && !ptr_btn) {
                ptr_btn = ei_device_ref(d);
                LOG("btn device: %s\n", ei_device_get_name(d));
            }
            if (ei_device_has_capability(d, EI_DEVICE_CAP_KEYBOARD) && !kbd) {
                kbd = ei_device_ref(d);
                LOG("kbd device: %s\n", ei_device_get_name(d));
            }
            break;
        }
        case EI_EVENT_DEVICE_RESUMED: {
            struct ei_device *d = ei_event_get_device(e);
            if (d == ptr_abs) { ei_device_start_emulating(ptr_abs, ++sequence); have_abs = 1; LOG("abs resumed\n"); }
            if (d == ptr_btn) { ei_device_start_emulating(ptr_btn, ++sequence); have_btn = 1; LOG("btn resumed\n"); }
            if (d == kbd)     { ei_device_start_emulating(kbd, ++sequence);     have_kbd = 1; LOG("kbd resumed\n"); }
            break;
        }
        case EI_EVENT_DEVICE_PAUSED: {
            struct ei_device *d = ei_event_get_device(e);
            if (d == ptr_abs) have_abs = 0;
            if (d == ptr_btn) have_btn = 0;
            if (d == kbd)     have_kbd = 0;
            break;
        }
        default: break;
        }
        ei_event_unref(e);
    }
}

/* Wait until at least an absolute-pointer device is resumed (ready to emit). */
static int wait_ready(int max_ms) {
    int waited = 0;
    while (waited < max_ms && !(have_abs && have_btn)) {
        pump_events(100);
        waited += 100;
    }
    return have_abs && have_btn;
}

static void do_move(double x, double y) {
    if (!have_abs) { LOG("move: abs ptr not ready\n"); return; }
    uint64_t now = ei_now(ei_ctx);
    ei_device_pointer_motion_absolute(ptr_abs, x, y);
    ei_device_frame(ptr_abs, now);
}

static void do_button(int btn, int press) {
    /* Prefer the abs-pointer device so motion + button live in one stream. */
    struct ei_device *d = ptr_abs ? ptr_abs : ptr_btn;
    if (!d) { LOG("button: device not ready\n"); return; }
    uint64_t now = ei_now(ei_ctx);
    ei_device_button_button(d, btn_code(btn), press ? true : false);
    ei_device_frame(d, now);
}

static void do_scroll(int dy) {
    /* Use the abs-pointer device (it has SCROLL cap by default in our seat). */
    struct ei_device *d = ptr_abs ? ptr_abs : ptr_btn;
    if (!d) { LOG("scroll: device not ready\n"); return; }
    uint64_t now = ei_now(ei_ctx);
    /* delta is in scroll units; one wheel notch is ~120 in discrete or ~10 in delta.
       gamescope's EIS_EVENT_SCROLL_DELTA goes straight to wlserver_mousewheel. */
    ei_device_scroll_delta(d, 0.0, (double)dy);
    ei_device_frame(d, now);
}

static void do_key(int code, int press) {
    if (!have_kbd) { LOG("key: kbd not ready\n"); return; }
    uint64_t now = ei_now(ei_ctx);
    ei_device_keyboard_key(kbd, code, press ? true : false);
    ei_device_frame(kbd, now);
}

static void msleep(int ms) {
    struct timespec ts = { .tv_sec = ms / 1000, .tv_nsec = (ms % 1000) * 1000000L };
    nanosleep(&ts, NULL);
}

int main(int argc, char **argv) {
    for (int i = 1; i < argc; i++)
        if (!strcmp(argv[i], "-v") || !strcmp(argv[i], "--verbose")) verbose = 1;

    ei_ctx = ei_new_sender(NULL);
    if (!ei_ctx) { fprintf(stderr, "ei_new_sender failed\n"); return 1; }
    if (verbose) ei_log_set_priority(ei_ctx, EI_LOG_PRIORITY_DEBUG);
    ei_configure_name(ei_ctx, "ll-ai-driver");

    int rc = ei_setup_backend_socket(ei_ctx, NULL);   /* uses $LIBEI_SOCKET */
    if (rc != 0) { fprintf(stderr, "ei_setup_backend_socket: %s\n", strerror(-rc)); return 1; }

    if (!wait_ready(5000)) {
        fprintf(stderr, "[ei] timeout waiting for devices (abs=%d btn=%d kbd=%d)\n",
                have_abs, have_btn, have_kbd);
        return 2;
    }
    fprintf(stdout, "READY abs=%d btn=%d kbd=%d\n", have_abs, have_btn, have_kbd);
    fflush(stdout);

    char line[256];
    while (fgets(line, sizeof(line), stdin)) {
        char *nl = strchr(line, '\n'); if (nl) *nl = 0;
        char cmd[32]; int a = 0, b = 0;
        if (sscanf(line, "%31s %d %d", cmd, &a, &b) < 1) continue;

        if (!strcmp(cmd, "move"))         do_move((double)a, (double)b);
        else if (!strcmp(cmd, "click"))   { do_button(a ? a : 1, 1); pump_events(15); do_button(a ? a : 1, 0); }
        else if (!strcmp(cmd, "down"))    do_button(a ? a : 1, 1);
        else if (!strcmp(cmd, "up"))      do_button(a ? a : 1, 0);
        else if (!strcmp(cmd, "key"))     { do_key(a, 1); pump_events(15); do_key(a, 0); }
        else if (!strcmp(cmd, "keydown")) do_key(a, 1);
        else if (!strcmp(cmd, "keyup"))   do_key(a, 0);
        else if (!strcmp(cmd, "scroll"))  do_scroll(a);
        else if (!strcmp(cmd, "sleep"))   msleep(a);
        else if (!strcmp(cmd, "bye"))     break;
        else { fprintf(stderr, "[ei] unknown cmd: %s\n", line); }

        pump_events(5);
        fprintf(stdout, "OK\n"); fflush(stdout);
    }

    if (ptr_abs) ei_device_close(ptr_abs);
    if (ptr_btn && ptr_btn != ptr_abs) ei_device_close(ptr_btn);
    if (kbd) ei_device_close(kbd);
    if (default_seat) ei_seat_unref(default_seat);
    ei_unref(ei_ctx);
    return 0;
}
