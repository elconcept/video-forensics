# Step 63: strict Linux GPU selection and per-file result history

Linux GPU vendors are now derived only from PCI display-class devices: VGA, 3D, or Display controllers. Intel Wi-Fi devices and AMD audio or chipset functions no longer cause Intel QSV or AMD GPU detection. A profile is selected only after both a matching display controller and a successful runtime backend probe.

The result hierarchy is changed to:

`work/results/<source-file-stem>/<UTC timestamp>/`

This keeps every run for one source under a stable first-level directory and enables later comparison across timestamps. Host profiles remain timestamped directly under `work/results` and are referenced by each run.
