# BLE forwarding and duplicate suppression (English)

This is based on the FreeRTOS worker from live-observed 4.3.1. Two original 31-byte BLE advertisements are captured using user-configured addresses. Home Assistant keeps receiving the sensor updates as before; only the Cerbo forwarding path applies duplicate suppression.

**Rule:** Changed advertisements are eligible for forwarding on the existing **3-second schedule**. If both sets of hex bytes equal those last successfully accepted by the GX (HTTP 2xx), repeat HTTPS calls are suppressed until a **15-second** periodic refresh. RSSI-only changes do not trigger an early POST but are included on the next refresh. Failed HTTP requests are retryable at the next scheduling opportunity without waiting for the refresh deadline.

The worker maintains at most one outstanding request, with no unbounded backlog. No send is attempted without fresh packets and a pairing token. The forwarding switch resets OFF on reboot. The original BLE bytes are preserved, rather than replacing them with derived Home Assistant readings.

**Important:** The new 15-second refresh policy and TLS verification have **not yet been soak-tested together against the GX**. Some firmware versions may expect a shorter update interval; measure GX visibility and receiver behavior before changing the refresh limit. HTTP 201 proves HTTP acceptance only.
