# Rclone capabilities (high-signal deltas)

1. **Sync**: one-way mirroring between local and cloud/remotes (source → destination) with deletions to match.
2. **Copy**: copy-only transfers between any supported remotes without deleting destination data.
3. **Move**: transfer plus delete on source (useful for archival or tiering workflows).
4. **Server-side copy/move**: remote-to-remote transfers that stay in the cloud when supported.
5. **Mount**: mount a remote as a local filesystem (read/write) with VFS caching options.
6. **Bisync**: bidirectional synchronization for keeping two locations in lockstep.
7. **Check**: verify file integrity between source and destination using checksums/size/time.
8. **Crypt**: transparent client-side encryption (file names and contents) on top of any remote.
9. **Serve**: expose a remote via HTTP, WebDAV, SFTP, FTP, or S3-compatible endpoints.
10. **Remote control (RC/rcd)**: JSON API server for programmatic orchestration and automation.
11. **Filtering**: include/exclude rules, regex, age/size filters, and file type filters.
12. **Bandwidth limiting**: throttle transfer rates globally or by schedule.
13. **Resumable transfers**: retry/resume interrupted uploads and downloads.
14. **Chunked uploads**: split large files for providers that require chunking.
15. **Change detection**: use hashes, modtimes, and size to detect differences efficiently.
16. **Deduplicate**: detect and resolve duplicate files on a remote.
17. **Listing/metadata**: structured listings (e.g., `lsjson`) for inventory and audit.
18. **Purge**: delete all files on a remote/path quickly and safely.
19. **Directory size reporting**: compute total bytes/files for paths or remotes.
20. **Cross-platform support**: consistent CLI behavior across Windows, macOS, and Linux.
