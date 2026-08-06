# Step 29: bare-host migration and host capability profile

This step implements the deployment change from Revision 3:

- removes Dockerfile, Compose, and the container smoke test
- removes the container CI job
- adds runtime host capability capture
- adds Linux and macOS native launchers
- records external tools as present or absent without aborting collection
- records FFmpeg version, build configuration, decoders, and hwaccels
- records platform-specific CPU, GPU, and driver diagnostics

Apply the migration once:

python3 migrate_bare_host.py
rm migrate_bare_host.py
