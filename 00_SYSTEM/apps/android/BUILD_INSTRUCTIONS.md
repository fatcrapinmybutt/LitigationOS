# LitigationOS Android — Build Instructions

## Prerequisites

- **Node.js** v18+ (current: v25.6.0)
- **Expo account** — free at [expo.dev](https://expo.dev)
- **Google Play Developer account** — only needed for production Play Store publishing ($25 one-time)
- **No local Android SDK required** — EAS builds in the cloud

## Setup

### 1. Install EAS CLI

```bash
npm install -g eas-cli
```

### 2. Login to Expo

```bash
eas login
```

### 3. Link Project to Expo

After logging in, update the `projectId` in `app.json`:

```json
"extra": {
  "eas": {
    "projectId": "your-actual-project-id"
  }
}
```

You can get your project ID by running:

```bash
eas init
```

## Building

### Build APK (Preview / Testing)

Generates a standalone `.apk` file you can install directly on any Android device:

```bash
eas build --platform android --profile preview
```

Or use the npm script:

```bash
npm run build:apk
```

### Build AAB (Production / Play Store)

Generates an `.aab` bundle for Google Play Store submission:

```bash
eas build --platform android --profile production
```

Or use the npm script:

```bash
npm run build:aab
```

## Build Profiles

Defined in `eas.json`:

| Profile | Output | Use Case |
|---------|--------|----------|
| `preview` | `.apk` | Direct install on devices, testing |
| `production` | `.aab` | Google Play Store upload |

## After Building

1. EAS will provide a download URL for the build artifact
2. For APK: download and install directly on Android device (enable "Install from unknown sources")
3. For AAB: upload to Google Play Console

## App Details

| Field | Value |
|-------|-------|
| Package Name | `com.litigationos.mobile` |
| App Name | LitigationOS |
| Slug | `litigation-os` |
| Scheme | `litigationos://` |
| SDK | Expo 52 |

## Troubleshooting

- **`eas: command not found`** — run `npm install -g eas-cli`
- **Build fails on credentials** — EAS will prompt to generate Android keystore automatically
- **Missing dependencies** — run `npm install` then `npx expo install --check`
- **Check project health** — run `npx expo-doctor`
