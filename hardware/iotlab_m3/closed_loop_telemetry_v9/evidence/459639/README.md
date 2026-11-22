# Native three-board radio feedback experiment 459639

Exact result: INCOMPLETE_KEEP_RAW.

Originally registered source M3-16/head, member M3-15, sink M3-18, three rounds, 500B application fragmentation. Source MAC callback attempt/success/duration can be reported over actual radio to sink. Only sink observations independently matching the original per-node serial MAC record count as validated physical probe feedback.

Issue: Independent raw-source/sink MAC telemetry audit nonzero; see audit_execution.log

Strict limits: fixed head-routing STATIC pilot, two sources, one sink. There is no updated original predictor, no conformal bound refit, no fresh-risk head search, no next-round adaptive route plan and no 41-node physical feedback or deadlines. Do NOT call this full ACR-MCR.
