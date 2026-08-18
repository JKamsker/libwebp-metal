# Backref cost/traceback executor refusal report

Status: **REFUSED BEFORE RUN**

Source commit: `355efae8dad9fc09717a4ccef874adf6bf6b2d6f`  
Frozen base parent: `3142ff3fe31cd1666c5615c5c4ee7dec2ef891f8`  
Untimed validation: passed with the frozen manifest and operator hashes.  
Timed pipeline: not invoked.  

The required AC-power preflight observed `Low Power Mode: Yes`. The executor
stopped fail-closed without changing power settings, acquiring the benchmark
lease, building either variant, generating the corpus, running correctness,
or launching a timed child. No samples, ratios, evaluation decision, or
resource record were produced. The separate timed-child stderr capture records
that no timed child was launched. Closed experiment evidence was not used.
