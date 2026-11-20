# Security review — November 19, 2026

This review starts from v0.5.0 and the supplied summary of 112 findings across 60 files. The original finding-by-finding export and scanner version were not supplied, so those exact counts and every W015–W020 row cannot be independently reproduced here. No broad scanner suppressions or credential-shaped renamings were added to hide findings.

## Triage

| Reported category | Assessment and action |
|---|---|
| W008: five high “embedded secret” examples | Git revision/checkpoint hashes identify public assets; `SYNTHETIC_KEY` is a test fixture; Hugging Face `token=False` disables credential use for those calls. These examples are not leaked credentials. Preserve the revision and integrity checks. |
| W012: external dependencies/URLs | XML namespace URIs do not cause requests. Documentation/comment URLs do not execute themselves. Setup intentionally downloads trusted public code/weights; these capabilities remain available and must be provisioned separately from processing private images. |
| W015–W020: reads, writes, subprocesses and deletion capabilities | A capability label alone does not establish an exploit. Reviewed subprocesses use explicit argument vectors without `shell=True`; the runtime runner deliberately executes configured local model code. Deletions reviewed in mesh preparation and conversion remove known artifacts inside the selected job directory, not arbitrary recursively selected paths. These operations remain necessary to the workflow. |
| Printer key over HTTP | Real credential exposure risk. Refuse it by default; support verified HTTPS, an optional trusted CA file and an explicit plaintext-transport opt-in for HTTP-only devices. |
| Imported post-processing commands | Additional confirmed risk from the source review. Reject nonempty post-processing settings in color templates, direct slicer project inputs and the selected slicing presets before export/launch. The Bambu converter continues stripping these settings. |
| 3MF decompression and XML input | Additional hardening: shared archive checks, bounded metadata/model reads and parser-level DTD/entity rejection. Invalid slicer artifacts produce a failed review report. |

The source revisions for TripoSR, Bambu conversion and the expected TRELLIS/DINO runtime remain pinned. TripoSR setup resolves the public Hugging Face model/config revisions on first setup, records those immutable revisions and file hashes, and verifies assets before later generation. Its segmentation setup is provided by the separately installed rembg package and records the downloaded asset hash. This is not a claim that every first download has a hardcoded, independently verified checksum. Downloaded code, weights, native libraries and their licenses remain third-party trust boundaries; a hash recorded after download does not establish publisher authenticity.

## Changed behavior

The printer helper retains its fixed three GET routes, explicit private/loopback IP restriction, response size/time limits, no redirects and no state-changing operations. `--https` enables normal certificate-chain/IP verification and defaults to port 443. `--ca-file` trusts an explicitly provided CA, without disabling verification. TLS failures stop the request and do not retry with HTTP. Neither credentials nor response bodies are copied into error reports.

An inherited `SNAPMAKER_API_KEY` now causes an HTTP invocation to fail before a connection is created. For an HTTP-only authenticated device, the user can explicitly authorize `--allow-insecure-api-key`. This is an acknowledgment of exposure, not encryption or a substitute for TLS. No printer authentication, certificate store or network settings are modified by the skill.

3MF limits are 10,000 members, 512 MiB per member and 2 GiB total declared decompressed size; project settings/target metadata have a 1 MiB read limit. Reads also stop at the actual per-member bound. Duplicate/case-ambiguous names, traversal/absolute/Windows-drive paths, NUL names and encrypted entries are rejected. Raw member names are checked before Windows normalization can disguise separators. Color/Bambu XML parsing rejects DTD/entity declarations, including encoded forms. G-code review has a 512 MiB per-artifact bound. Large legitimate projects may need a separate reviewed workflow; do not bypass checks merely to make an import pass.

Post-processing commands are rejected, not silently edited out of calibrated color templates. Empty native settings remain valid. Required machine/filament G-code is not removed by this generic check; review it in Orca before printing. These checks are not a complete sanitizer for every possible native-slicer project extension or future format feature.

## Verification and remaining limits

Regression tests cover refused plaintext keys before connection, verified TLS contexts, failure without HTTP fallback, key redaction, explicit opt-in, malformed/oversized archives, encoded XML declarations, command-bearing templates/projects/presets, output preservation and failed artifact reporting. All fixtures are synthetic; tests do not contact a printer, execute a post-processing command or allocate a decompression bomb. CI runs the portable suite on Linux, Windows and macOS.

The anonymous HTTP printer snapshot remains plaintext and unauthenticated at the transport layer. A snapshot is not an interlock or print-readiness certification. Configured runtimes execute with the local user's permissions; the Python socket guard is not an OS-wide sandbox. Native Orca, optional model inference, third-party binaries/packages and a real printer HTTPS endpoint require separate validation. No claim is made that the original scanner will report zero findings, or that this review exhaustively checks every release artifact and Git-history secret.

Relevant upstream behavior: [Python HTTPS certificate verification](https://docs.python.org/3/library/http.client.html#http.client.HTTPSConnection), [secure SSL contexts](https://docs.python.org/3/library/ssl.html#ssl.create_default_context), and [Snapmaker Orca post-processing execution](https://github.com/Snapmaker/OrcaSlicer/blob/main/src/libslic3r/GCode/PostProcessor.cpp).
