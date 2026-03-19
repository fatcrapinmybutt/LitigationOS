def register(registry):
    def tweak(report: dict)->dict:
        fn = report.get("filename","").lower()
        if "screenshot" in fn:
            report["auth_901_902"] = "needs_foundation"
        return report
    registry.setdefault("admissibility_hooks", []).append(tweak)
