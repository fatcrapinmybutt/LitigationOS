"""
Shell Action Handler — invoked by Windows right-click context menu.
Usage: python _shell_action.py <action_id> <file_path>

Sends the action to the running daemon via IPC.
Shows result via toast notification.
"""
import os
import sys

# Ensure parent package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def main():
    if len(sys.argv) < 3:
        print("Usage: python _shell_action.py <action_id> <file_path>")
        sys.exit(1)

    action_id = sys.argv[1]
    file_path = sys.argv[2]

    from daemon.shell_integration import ShellAction, ToastNotifier

    action = ShellAction()
    result = action.execute(action_id, file_path)

    # Show notification
    if result.get("success"):
        ToastNotifier.notify(
            "LitigationOS",
            f"✓ {action_id}: {os.path.basename(file_path)} queued"
        )
    else:
        ToastNotifier.notify(
            "LitigationOS Error",
            f"✗ {result.get('error', 'Unknown error')}"
        )


if __name__ == "__main__":
    main()
