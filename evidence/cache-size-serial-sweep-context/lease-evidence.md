# Cache-size serial-sweep lease evidence

Lease path from the frozen manifest:

```text
/tmp/libwebp-metal-cache-size-serial-sweep.lock
```

The preflight `lsof -nP /tmp/libwebp-metal-cache-size-serial-sweep.lock`
returned no rows, so no holder was observed before execution. While the
operator process was active, the exact observed lease descriptor was:

```text
COMMAND   PID         USER   FD   TYPE DEVICE SIZE/OFF    NODE NAME
Python  41911 jonaskamsker    4u   REG   1,15        0 1362176 /private/tmp/libwebp-metal-cache-size-serial-sweep.lock
```

The operator uses the frozen nonblocking `fcntl.flock(LOCK_EX | LOCK_NB)`
acquisition. After the command exited 0, the same `lsof` query returned no
rows. The frozen resources report records:

```json
{"lease_released": true}
```

No lease was held when this evidence was committed or when the final report
was returned.
