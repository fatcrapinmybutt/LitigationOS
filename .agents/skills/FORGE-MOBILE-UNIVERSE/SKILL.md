---
name: FORGE-MOBILE-UNIVERSE
description: >-
  Universal mobile development superskill that fuses cross-platform React Native,
  Flutter, PWA, architecture patterns, testing matrices, CI/CD pipelines, and
  security hardening into a single coherent system. Write one feature specification
  and generate native iOS (Swift/SwiftUI), Android (Kotlin/Compose), React Native,
  Flutter, AND PWA implementations simultaneously with shared business logic,
  platform-optimized UI, unified testing, and a single deployment pipeline
  targeting all five platforms.
category: engineering
version: "1.0.0"
triggers:
  - "mobile app"
  - "cross-platform"
  - "react native"
  - "flutter"
  - "progressive web app"
  - "mobile architecture"
  - "mobile testing"
  - "mobile ci cd"
  - "mobile security"
  - "app deployment"
  - "platform transcendence"
  - "universal mobile"
metadata:
  tier: FORGE
  fused_skills: 8
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: "2026-03-27"
  forge_class: cross-domain-innovation
  emergent_capability: >-
    Universal Platform Transcendence — write a single feature specification and
    generate native iOS (Swift/SwiftUI), Android (Kotlin/Compose), React Native,
    Flutter, AND PWA implementations simultaneously. Shared business logic,
    platform-optimized UI, unified testing, single CI/CD pipeline deploying to
    all 5 targets.
---

# 📱 FORGE-MOBILE-UNIVERSE
### *(Ω-Δ99)*

> **The Universal Mobile Development Forge** — a cross-domain fusion of eight
> specialized mobile skills into one orchestrated superskill capable of
> transcending individual platform boundaries.
>
> | Attribute | Value |
> |-----------|-------|
> | **Tier** | FORGE (Fused Orchestrated Reasoning for Generative Engineering) |
> | **Domain** | Mobile · Cross-Platform · PWA · Native · Architecture |
> | **Scope** | iOS · Android · React Native · Flutter · Web (PWA) |
> | **Emergent** | Universal Platform Transcendence — 1 spec → 5 platforms |

---

## 🔬 Forged from 8 Skills

| # | Source Skill | Domain | Key Contribution |
|---|-------------|--------|-----------------|
| 1 | `react-native-master` | Cross-platform JS/TS | Expo, bare workflow, native modules, Reanimated |
| 2 | `flutter-forge` | Cross-platform Dart | Widgets, Riverpod, GoRouter, platform channels |
| 3 | `mobile-architecture` | Patterns | Clean architecture, MVVM, BLoC, Redux, unidirectional |
| 4 | `mobile-performance` | Optimization | Bundle splitting, lazy loading, memory mgmt, profiling |
| 5 | `mobile-testing` | Quality assurance | Detox, Maestro, Appium, XCTest, Espresso |
| 6 | `mobile-ci-cd` | DevOps | Fastlane, store deployment, code signing, OTA |
| 7 | `mobile-security` | Security | Cert pinning, secure storage, biometric auth, obfuscation |
| 8 | `progressive-web-app` | Web platform | Service workers, offline-first, installable apps, Workbox |

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FORGE-MOBILE-UNIVERSE (Ω-Δ99)                        │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    MU1: PLATFORM ABSTRACTION CORE                │   │
│  │         Shared Business Logic · Domain Models · Use Cases        │   │
│  │            TypeScript / Dart / Kotlin Multiplatform              │   │
│  └──────┬──────────────┬──────────────┬──────────────┬─────────────┘   │
│         │              │              │              │                   │
│         ▼              ▼              ▼              ▼                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐          │
│  │    MU2     │ │    MU3     │ │    MU4     │ │  NATIVE    │          │
│  │   React    │ │  Flutter   │ │    PWA     │ │  iOS/Droid │          │
│  │  Native    │ │  Fusion    │ │ Synthesis  │ │  (Swift/   │          │
│  │  Reactor   │ │  Engine    │ │            │ │  Kotlin)   │          │
│  └──────┬─────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘          │
│         │              │              │              │                   │
│         ▼              ▼              ▼              ▼                   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              MU5: MOBILE ARCHITECTURE PATTERNS                   │   │
│  │     Clean Arch · MVVM · BLoC · Unidirectional Data Flow         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│         │              │              │                                  │
│         ▼              ▼              ▼                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                         │
│  │    MU6     │ │    MU7     │ │    MU8     │                         │
│  │  Testing   │ │ Deployment │ │  Security  │                         │
│  │  Matrix    │ │  Pipeline  │ │ Hardening  │                         │
│  └────────────┘ └────────────┘ └────────────┘                         │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════    │
│  EMERGENT: 1 Feature Spec → 5 Platform Outputs (iOS/Android/RN/Fl/PWA)│
│  ═══════════════════════════════════════════════════════════════════    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## MU1: Platform Abstraction Core

**Purpose:** Define shared business logic, domain models, use cases, and data
contracts that every platform target consumes without modification. The core is
the single source of truth — platform layers are thin adapters.

**Design Pattern:** *Hexagonal Architecture (Ports & Adapters)* — domain logic
has zero dependencies on any framework. Platform targets implement the "ports"
as adapters.

### Core Domain Model (TypeScript — shared via codegen)

```typescript
// core/domain/models/User.ts
export interface User {
  id: string;
  email: string;
  displayName: string;
  avatarUrl?: string;
  preferences: UserPreferences;
  createdAt: Date;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  notificationsEnabled: boolean;
  biometricAuthEnabled: boolean;
  offlineModeEnabled: boolean;
}

// core/domain/models/Result.ts
export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };
```

### Use Case (Framework-Agnostic)

```typescript
// core/usecases/AuthenticateUser.ts
import { User, Result } from '../domain/models';

export interface AuthPort {
  signIn(email: string, password: string): Promise<Result<User>>;
  signOut(): Promise<Result<void>>;
  refreshToken(): Promise<Result<string>>;
  getBiometricCredential(): Promise<Result<{ email: string; password: string }>>;
}

export interface StoragePort {
  setSecure(key: string, value: string): Promise<void>;
  getSecure(key: string): Promise<string | null>;
  deleteSecure(key: string): Promise<void>;
}

export class AuthenticateUser {
  constructor(
    private auth: AuthPort,
    private storage: StoragePort,
  ) {}

  async execute(email: string, password: string): Promise<Result<User>> {
    const result = await this.auth.signIn(email, password);
    if (result.ok) {
      await this.storage.setSecure('auth_token', JSON.stringify(result.value));
    }
    return result;
  }

  async biometricLogin(): Promise<Result<User>> {
    const cred = await this.auth.getBiometricCredential();
    if (!cred.ok) return cred;
    return this.execute(cred.value.email, cred.value.password);
  }
}
```

### Spec-to-Platform Codegen Schema

```yaml
# specs/features/user-auth.feature.yaml
feature: user-authentication
version: 1
platforms: [ios, android, react-native, flutter, pwa]
domain_model: User
use_case: AuthenticateUser
ui_spec:
  screen: LoginScreen
  fields:
    - { name: email, type: email, validation: required|email }
    - { name: password, type: password, validation: required|min:8 }
  actions:
    - { label: "Sign In", triggers: AuthenticateUser.execute }
    - { label: "Use Biometrics", triggers: AuthenticateUser.biometricLogin }
  navigation:
    on_success: HomeScreen
    on_failure: show_error_toast
```

**Integration Points:** MU1 feeds directly into MU2 (React Native adapters),
MU3 (Flutter adapters), MU4 (PWA adapters), and native iOS/Android targets.
MU5 consumes the domain models for architecture wiring.

---

## MU2: React Native Reactor

**Purpose:** Full React Native development — Expo managed + bare workflow,
native modules, Reanimated animations, and platform-specific bridges.

**Design Pattern:** *Feature-Sliced Architecture* — each feature is a
self-contained vertical slice with its own UI, state, and API layer consuming
MU1 core logic via dependency injection.

### Expo + React Native Screen (consuming MU1 core)

```tsx
// src/features/auth/screens/LoginScreen.tsx
import React, { useState, useCallback } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, Alert,
} from 'react-native';
import Animated, {
  useSharedValue, useAnimatedStyle, withSpring, withSequence,
} from 'react-native-reanimated';
import * as LocalAuthentication from 'expo-local-authentication';
import { AuthenticateUser } from '@core/usecases/AuthenticateUser';
import { useInjection } from '../di/useInjection';

export const LoginScreen: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const auth = useInjection<AuthenticateUser>('AuthenticateUser');
  const shakeX = useSharedValue(0);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: shakeX.value }],
  }));

  const handleLogin = useCallback(async () => {
    setLoading(true);
    const result = await auth.execute(email, password);
    setLoading(false);
    if (!result.ok) {
      shakeX.value = withSequence(
        withSpring(10), withSpring(-10), withSpring(10), withSpring(0),
      );
    }
  }, [email, password, auth, shakeX]);

  const handleBiometric = useCallback(async () => {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    if (!compatible) return Alert.alert('Biometrics not available');
    const authResult = await LocalAuthentication.authenticateAsync({
      promptMessage: 'Authenticate to sign in',
      fallbackLabel: 'Use password',
    });
    if (authResult.success) {
      setLoading(true);
      await auth.biometricLogin();
      setLoading(false);
    }
  }, [auth]);

  return (
    <Animated.View style={[styles.container, animatedStyle]}>
      <Text style={styles.title}>Welcome Back</Text>
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
        accessibilityLabel="Email input"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        accessibilityLabel="Password input"
      />
      <TouchableOpacity
        style={styles.button}
        onPress={handleLogin}
        disabled={loading}
        accessibilityRole="button"
      >
        <Text style={styles.buttonText}>
          {loading ? 'Signing in…' : 'Sign In'}
        </Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={handleBiometric} style={styles.biometric}>
        <Text style={styles.biometricText}>🔐 Use Biometrics</Text>
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 24 },
  title: { fontSize: 28, fontWeight: '700', marginBottom: 32, textAlign: 'center' },
  input: {
    borderWidth: 1, borderColor: '#ddd', borderRadius: 12,
    padding: 16, marginBottom: 16, fontSize: 16,
  },
  button: {
    backgroundColor: '#007AFF', borderRadius: 12, padding: 16,
    alignItems: 'center', marginTop: 8,
  },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '600' },
  biometric: { alignItems: 'center', marginTop: 24 },
  biometricText: { fontSize: 16, color: '#007AFF' },
});
```

### Native Module Bridge (Turbo Module)

```typescript
// src/native/SecureStorageModule.ts
import { TurboModule, TurboModuleRegistry } from 'react-native';

export interface Spec extends TurboModule {
  setSecureItem(key: string, value: string): Promise<void>;
  getSecureItem(key: string): Promise<string | null>;
  deleteSecureItem(key: string): Promise<void>;
  isBiometricAvailable(): Promise<boolean>;
}

export default TurboModuleRegistry.getEnforcing<Spec>('SecureStorage');
```

**Integration Points:** Consumes MU1 use cases via DI container. MU5
architecture patterns shape state management. MU6 runs Detox E2E against this
layer. MU7 builds via Fastlane + EAS. MU8 wraps secure storage and cert
pinning.

---

## MU3: Flutter Fusion Engine

**Purpose:** Complete Flutter development with Riverpod state management,
GoRouter navigation, platform channels for native access, and Material 3 /
Cupertino adaptive UI.

**Design Pattern:** *Feature-First with Riverpod* — each feature folder
contains its own providers, widgets, and repository implementations consuming
MU1 domain models mapped to Dart.

### Flutter Login Screen (consuming MU1 core via Dart mapping)

```dart
// lib/features/auth/presentation/login_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../domain/auth_state.dart';
import '../providers/auth_providers.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen>
    with SingleTickerProviderStateMixin {
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  late final AnimationController _shakeCtrl;
  late final Animation<double> _shakeAnim;

  @override
  void initState() {
    super.initState();
    _shakeCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _shakeAnim = Tween(begin: 0.0, end: 10.0).chain(
      CurveTween(curve: Curves.elasticIn),
    ).animate(_shakeCtrl);
  }

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    _shakeCtrl.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;
    final notifier = ref.read(authNotifierProvider.notifier);
    await notifier.signIn(_emailCtrl.text, _passwordCtrl.text);
    final state = ref.read(authNotifierProvider);
    if (state is AuthError) {
      _shakeCtrl.forward(from: 0);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(state.message)),
        );
      }
    } else if (state is Authenticated) {
      if (mounted) context.go('/home');
    }
  }

  Future<void> _handleBiometric() async {
    final notifier = ref.read(authNotifierProvider.notifier);
    await notifier.biometricLogin();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final isLoading = authState is AuthLoading;

    return Scaffold(
      body: AnimatedBuilder(
        animation: _shakeAnim,
        builder: (context, child) => Transform.translate(
          offset: Offset(_shakeAnim.value, 0),
          child: child,
        ),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text('Welcome Back',
                    style: Theme.of(context).textTheme.headlineLarge),
                const SizedBox(height: 32),
                TextFormField(
                  controller: _emailCtrl,
                  decoration: const InputDecoration(labelText: 'Email'),
                  keyboardType: TextInputType.emailAddress,
                  validator: (v) =>
                      v != null && v.contains('@') ? null : 'Invalid email',
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordCtrl,
                  decoration: const InputDecoration(labelText: 'Password'),
                  obscureText: true,
                  validator: (v) => v != null && v.length >= 8
                      ? null : 'Min 8 characters',
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: isLoading ? null : _handleLogin,
                  child: isLoading
                      ? const CircularProgressIndicator()
                      : const Text('Sign In'),
                ),
                const SizedBox(height: 16),
                TextButton.icon(
                  onPressed: _handleBiometric,
                  icon: const Icon(Icons.fingerprint),
                  label: const Text('Use Biometrics'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

### Riverpod Auth Provider

```dart
// lib/features/auth/providers/auth_providers.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/auth_state.dart';
import '../../../core/usecases/authenticate_user.dart';

final authNotifierProvider =
    StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.watch(authenticateUserProvider));
});

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthenticateUser _authenticateUser;

  AuthNotifier(this._authenticateUser) : super(const AuthInitial());

  Future<void> signIn(String email, String password) async {
    state = const AuthLoading();
    final result = await _authenticateUser.execute(email, password);
    state = result.fold(
      (user) => Authenticated(user),
      (error) => AuthError(error.message),
    );
  }

  Future<void> biometricLogin() async {
    state = const AuthLoading();
    final result = await _authenticateUser.biometricLogin();
    state = result.fold(
      (user) => Authenticated(user),
      (error) => AuthError(error.message),
    );
  }
}
```

### Platform Channel (Flutter → Native)

```dart
// lib/core/platform/secure_storage_channel.dart
import 'package:flutter/services.dart';

class SecureStorageChannel {
  static const _channel = MethodChannel('com.app/secure_storage');

  Future<void> setSecure(String key, String value) =>
      _channel.invokeMethod('setSecure', {'key': key, 'value': value});

  Future<String?> getSecure(String key) =>
      _channel.invokeMethod<String>('getSecure', {'key': key});

  Future<void> deleteSecure(String key) =>
      _channel.invokeMethod('deleteSecure', {'key': key});
}
```

**Integration Points:** MU1 domain models are mapped to Dart data classes.
MU5 dictates Riverpod + clean arch layering. MU6 runs widget tests + integration
tests. MU7 deploys via Fastlane for both iOS/Android. MU8 provides platform
channel security.

---

## MU4: Progressive Web Synthesis

**Purpose:** Build installable, offline-first Progressive Web Apps using service
workers, Workbox, Web App Manifest, and the Cache API for full feature parity
with native targets.

**Design Pattern:** *App Shell + Offline-First* — cache the application shell
immediately, lazy-load feature modules, use IndexedDB for offline data, and
Background Sync for queued mutations.

### Web App Manifest

```json
{
  "name": "Universal App",
  "short_name": "UniApp",
  "description": "Cross-platform application — works everywhere",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#007AFF",
  "orientation": "portrait-primary",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    {
      "src": "/icons/icon-maskable-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],
  "screenshots": [
    { "src": "/screenshots/wide.png", "sizes": "1280x720", "type": "image/png", "form_factor": "wide" },
    { "src": "/screenshots/narrow.png", "sizes": "750x1334", "type": "image/png", "form_factor": "narrow" }
  ],
  "share_target": {
    "action": "/share",
    "method": "POST",
    "enctype": "multipart/form-data",
    "params": { "title": "title", "text": "text", "url": "url" }
  }
}
```

### Service Worker with Workbox

```javascript
// src/sw.js
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { BackgroundSyncPlugin } from 'workbox-background-sync';

// Precache app shell
precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

// Cache API responses with network-first strategy
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 60 * 60 }),
    ],
  }),
);

// Cache static assets with cache-first
registerRoute(
  ({ request }) =>
    request.destination === 'image' ||
    request.destination === 'font' ||
    request.destination === 'style',
  new CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new ExpirationPlugin({ maxEntries: 200, maxAgeSeconds: 30 * 24 * 60 * 60 }),
    ],
  }),
);

// Background sync for offline mutations
const bgSyncPlugin = new BackgroundSyncPlugin('mutation-queue', {
  maxRetentionTime: 24 * 60, // 24 hours
});

registerRoute(
  ({ url }) => url.pathname.startsWith('/api/mutations'),
  new NetworkFirst({ plugins: [bgSyncPlugin] }),
  'POST',
);

// Offline fallback
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/offline.html')),
    );
  }
});
```

### PWA Login Component (consuming MU1 core)

```typescript
// src/features/auth/LoginScreen.ts
import { AuthenticateUser } from '@core/usecases/AuthenticateUser';
import { WebAuthnAdapter } from '../adapters/WebAuthnAdapter';

class LoginScreen extends HTMLElement {
  private auth: AuthenticateUser;

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.auth = new AuthenticateUser(
      new FetchAuthAdapter(),
      new IndexedDBStorageAdapter(),
    );
  }

  connectedCallback() {
    this.render();
    this.shadowRoot!.querySelector('form')!
      .addEventListener('submit', (e) => this.handleSubmit(e));
    this.shadowRoot!.querySelector('#biometric')!
      .addEventListener('click', () => this.handleBiometric());
  }

  private async handleSubmit(e: Event) {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const data = new FormData(form);
    const result = await this.auth.execute(
      data.get('email') as string,
      data.get('password') as string,
    );
    if (result.ok) window.location.href = '/home';
    else this.showError(result.error.message);
  }

  private async handleBiometric() {
    if (!window.PublicKeyCredential) return;
    const result = await this.auth.biometricLogin();
    if (result.ok) window.location.href = '/home';
  }

  private showError(msg: string) {
    const el = this.shadowRoot!.querySelector('.error') as HTMLElement;
    el.textContent = msg;
    el.style.display = 'block';
    el.animate([
      { transform: 'translateX(-10px)' }, { transform: 'translateX(10px)' },
      { transform: 'translateX(-5px)' },  { transform: 'translateX(0)' },
    ], { duration: 300, easing: 'ease-out' });
  }

  private render() {
    this.shadowRoot!.innerHTML = `
      <style>
        :host { display: flex; justify-content: center; align-items: center;
                min-height: 100vh; font-family: system-ui; }
        form { width: 100%; max-width: 400px; padding: 2rem; }
        input { width: 100%; padding: 1rem; margin-bottom: 1rem;
                border: 1px solid #ddd; border-radius: 12px; font-size: 1rem; }
        button { width: 100%; padding: 1rem; border: none; border-radius: 12px;
                 background: #007AFF; color: white; font-size: 1.1rem; cursor: pointer; }
        .error { display: none; color: #e74c3c; margin-bottom: 1rem; text-align: center; }
      </style>
      <form>
        <h1>Welcome Back</h1>
        <div class="error"></div>
        <input name="email" type="email" placeholder="Email" required />
        <input name="password" type="password" placeholder="Password"
               minlength="8" required />
        <button type="submit">Sign In</button>
        <button type="button" id="biometric">🔐 Use Biometrics</button>
      </form>
    `;
  }
}

customElements.define('login-screen', LoginScreen);
```

**Integration Points:** MU1 core via ES modules or bundled adapters. MU5
architecture applies to PWA state (Redux-like stores). MU6 tests via Playwright
for web. MU7 deploys via CI to CDN/edge. MU8 handles HTTPS enforcement, CSP
headers, and credential storage.

---

## MU5: Mobile Architecture Patterns

**Purpose:** Enforce clean, testable, maintainable architecture across all
platform targets with consistent layering, state management, and dependency
injection patterns.

**Design Pattern:** *Layered Clean Architecture* — Presentation → Domain →
Data, with unidirectional data flow across all frameworks.

### Architecture Layer Map

```
┌─────────────────────────────────────────────┐
│           PRESENTATION LAYER                │
│  ┌─────────┬─────────┬─────────┬──────────┐ │
│  │ RN View │ Flutter │  PWA    │  Native  │ │
│  │  (JSX)  │ Widget  │ WebComp │ (UIKit/  │ │
│  │         │         │         │ Compose) │ │
│  └────┬────┴────┬────┴────┬────┴────┬─────┘ │
│       └─────────┴─────────┴─────────┘       │
│                    │ ViewModel / BLoC        │
├────────────────────┼────────────────────────┤
│           DOMAIN LAYER (MU1 Core)           │
│  Use Cases · Entities · Repository Ports     │
├────────────────────┼────────────────────────┤
│           DATA LAYER                        │
│  API Clients · Local DB · Cache · Mappers    │
└─────────────────────────────────────────────┘
```

### MVVM ViewModel (Kotlin — Android native target)

```kotlin
// features/auth/presentation/LoginViewModel.kt
class LoginViewModel(
    private val authenticateUser: AuthenticateUser,
    private val savedStateHandle: SavedStateHandle,
) : ViewModel() {

    private val _uiState = MutableStateFlow<LoginUiState>(LoginUiState.Idle)
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    fun signIn(email: String, password: String) {
        viewModelScope.launch {
            _uiState.value = LoginUiState.Loading
            val result = authenticateUser.execute(email, password)
            _uiState.value = when {
                result.isSuccess -> LoginUiState.Success(result.getOrThrow())
                else -> LoginUiState.Error(result.exceptionOrNull()?.message ?: "Unknown error")
            }
        }
    }

    fun biometricLogin() {
        viewModelScope.launch {
            _uiState.value = LoginUiState.Loading
            val result = authenticateUser.biometricLogin()
            _uiState.value = when {
                result.isSuccess -> LoginUiState.Success(result.getOrThrow())
                else -> LoginUiState.Error(result.exceptionOrNull()?.message ?: "Unknown error")
            }
        }
    }
}

sealed interface LoginUiState {
    data object Idle : LoginUiState
    data object Loading : LoginUiState
    data class Success(val user: User) : LoginUiState
    data class Error(val message: String) : LoginUiState
}
```

### SwiftUI View (iOS native target)

```swift
// Features/Auth/Presentation/LoginView.swift
import SwiftUI
import LocalAuthentication

struct LoginView: View {
    @StateObject private var viewModel: LoginViewModel
    @State private var email = ""
    @State private var password = ""
    @State private var shake = false

    var body: some View {
        VStack(spacing: 24) {
            Text("Welcome Back")
                .font(.largeTitle).bold()

            TextField("Email", text: $email)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.emailAddress)
                .textContentType(.emailAddress)
                .autocapitalization(.none)

            SecureField("Password", text: $password)
                .textFieldStyle(.roundedBorder)
                .textContentType(.password)

            Button(action: { Task { await signIn() } }) {
                if viewModel.isLoading {
                    ProgressView()
                } else {
                    Text("Sign In").frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isLoading)

            Button("🔐 Use Biometrics") { Task { await biometricLogin() } }
                .foregroundColor(.accentColor)
        }
        .padding(24)
        .offset(x: shake ? 10 : 0)
        .animation(.default.repeatCount(3, autoreverses: true), value: shake)
    }

    private func signIn() async {
        await viewModel.signIn(email: email, password: password)
        if viewModel.hasError { shake.toggle() }
    }

    private func biometricLogin() async {
        let context = LAContext()
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: nil) else { return }
        do {
            let success = try await context.evaluatePolicy(
                .deviceOwnerAuthenticationWithBiometrics, localizedReason: "Sign in"
            )
            if success { await viewModel.biometricLogin() }
        } catch { /* handle error */ }
    }
}
```

**Integration Points:** Every MU2/MU3/MU4 screen and every native target
follows MU5 patterns. MU1 provides the domain layer. MU6 tests the ViewModel
layer directly. MU8 security patterns integrate at the data layer.

---

## MU6: Cross-Platform Testing Matrix

**Purpose:** Unified testing strategy covering unit, widget/component,
integration, and E2E tests across all five platform targets with a single test
specification producing framework-specific test code.

**Design Pattern:** *Test Pyramid + Behavioral Contracts* — shared behavioral
assertions, platform-specific runners.

### Test Strategy Matrix

```
┌─────────────┬─────────────┬──────────────┬──────────────┬────────────┐
│   Level     │ React Native│   Flutter    │     PWA      │  Native    │
├─────────────┼─────────────┼──────────────┼──────────────┼────────────┤
│ Unit        │ Jest        │ flutter_test │ Vitest       │ XCTest /   │
│             │             │              │              │ JUnit5     │
├─────────────┼─────────────┼──────────────┼──────────────┼────────────┤
│ Component   │ RNTL        │ Widget test  │ Testing Lib  │ ViewInspec │
│             │             │              │              │ /Espresso  │
├─────────────┼─────────────┼──────────────┼──────────────┼────────────┤
│ Integration │ Detox       │ integration  │ Playwright   │ XCUITest / │
│             │             │ _test        │              │ UIAutomator│
├─────────────┼─────────────┼──────────────┼──────────────┼────────────┤
│ E2E         │ Maestro     │ Maestro      │ Maestro Web  │ Maestro    │
│             │             │              │              │            │
├─────────────┼─────────────┼──────────────┼──────────────┼────────────┤
│ Visual      │ Storybook + │ Golden tests │ Chromatic    │ Snapshot   │
│ Regression  │ Chromatic   │              │              │ tests      │
└─────────────┴─────────────┴──────────────┴──────────────┴────────────┘
```

### Detox E2E Test (React Native)

```typescript
// e2e/auth/login.e2e.ts
import { device, element, by, expect } from 'detox';

describe('Login Flow', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should login with valid credentials', async () => {
    await element(by.label('Email input')).typeText('user@example.com');
    await element(by.label('Password input')).typeText('securePass123');
    await element(by.text('Sign In')).tap();
    await expect(element(by.text('Welcome, User'))).toBeVisible();
  });

  it('should shake on invalid credentials', async () => {
    await element(by.label('Email input')).typeText('bad@example.com');
    await element(by.label('Password input')).typeText('wrong');
    await element(by.text('Sign In')).tap();
    await expect(element(by.label('Email input'))).toBeVisible();
  });
});
```

### Maestro Cross-Platform Flow (runs on RN, Flutter, AND native)

```yaml
# .maestro/auth/login-flow.yaml
appId: com.example.universalapp
---
- launchApp
- tapOn: "Email"
- inputText: "user@example.com"
- tapOn: "Password"
- inputText: "securePass123"
- tapOn: "Sign In"
- assertVisible: "Welcome"
- tapOn: "Settings"
- assertVisible: "Account"
```

### Flutter Widget Test

```dart
// test/features/auth/login_screen_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mocktail/mocktail.dart';
import 'package:app/features/auth/presentation/login_screen.dart';

class MockAuthenticateUser extends Mock implements AuthenticateUser {}

void main() {
  late MockAuthenticateUser mockAuth;

  setUp(() => mockAuth = MockAuthenticateUser());

  testWidgets('shows error on invalid credentials', (tester) async {
    when(() => mockAuth.execute(any(), any()))
        .thenAnswer((_) async => Result.error('Invalid credentials'));

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authenticateUserProvider.overrideWithValue(mockAuth),
        ],
        child: const MaterialApp(home: LoginScreen()),
      ),
    );

    await tester.enterText(find.byType(TextFormField).first, 'bad@email.com');
    await tester.enterText(find.byType(TextFormField).last, 'wrongpwd');
    await tester.tap(find.text('Sign In'));
    await tester.pumpAndSettle();

    expect(find.text('Invalid credentials'), findsOneWidget);
  });
}
```

**Integration Points:** MU6 tests every layer produced by MU2, MU3, MU4, and
native targets. MU7 CI/CD pipeline runs the full matrix. MU1 core logic has its
own pure unit tests. MU8 security tests (cert pinning, storage) are specialized
E2E flows within MU6.

---

## MU7: Deployment Pipeline

**Purpose:** Single CI/CD pipeline that builds, tests, signs, and deploys all
five platform targets from one trigger — Fastlane for native stores, EAS for
React Native, Shorebird for Flutter OTA, and CDN for PWA.

**Design Pattern:** *Monorepo Pipeline Fan-Out* — one commit triggers parallel
builds for all targets, converging at a release gate.

### Pipeline Architecture

```
          ┌─────── git push / tag ───────┐
          │                              │
          ▼                              │
    ┌───────────┐                        │
    │  CI Gate  │  lint + unit tests     │
    └─────┬─────┘                        │
          │ (pass)                       │
     ┌────┼────┬────┬────┐              │
     ▼    ▼    ▼    ▼    ▼              │
   [iOS] [And] [RN] [Fl] [PWA]         │
   Build  Build Build Build Build       │
     │    │    │    │    │              │
     ▼    ▼    ▼    ▼    ▼              │
   Sign  Sign  EAS  Sign  ---          │
     │    │    │    │    │              │
     ▼    ▼    ▼    ▼    ▼              │
   [E2E Test Matrix — MU6]             │
     │                                  │
     ▼                                  │
   ┌─────────────┐                      │
   │ Release Gate│ manual approval      │
   └──────┬──────┘                      │
     ┌────┼────┬────┬────┐              │
     ▼    ▼    ▼    ▼    ▼              │
   App  Play  EAS  Shore CDN            │
   Store Store OTA  bird  Deploy        │
          │                              │
          └── Release Notes ─────────────┘
```

### Fastlane Configuration

```ruby
# fastlane/Fastfile
default_platform(:ios)

platform :ios do
  desc "Build and deploy to TestFlight"
  lane :beta do
    setup_ci
    match(type: "appstore", readonly: true)
    increment_build_number(
      build_number: ENV["CI_BUILD_NUMBER"] || latest_testflight_build_number + 1,
    )
    build_app(
      workspace: "ios/App.xcworkspace",
      scheme: "App",
      export_method: "app-store",
      output_directory: "./build",
    )
    upload_to_testflight(skip_waiting_for_build_processing: true)
    slack(message: "iOS beta deployed to TestFlight 🚀")
  end

  lane :release do
    beta
    upload_to_app_store(
      skip_screenshots: true,
      submit_for_review: true,
      automatic_release: false,
      precheck_include_in_app_purchases: false,
    )
  end
end

platform :android do
  desc "Build and deploy to Play Store internal track"
  lane :beta do
    gradle(
      project_dir: "android",
      task: "bundle",
      build_type: "Release",
      properties: {
        "android.injected.signing.store.file" => ENV["KEYSTORE_PATH"],
        "android.injected.signing.store.password" => ENV["KEYSTORE_PASSWORD"],
        "android.injected.signing.key.alias" => ENV["KEY_ALIAS"],
        "android.injected.signing.key.password" => ENV["KEY_PASSWORD"],
      },
    )
    upload_to_play_store(
      track: "internal",
      aab: "android/app/build/outputs/bundle/release/app-release.aab",
    )
    slack(message: "Android beta deployed to Play Store internal 🚀")
  end
end
```

### GitHub Actions Unified Pipeline

```yaml
# .github/workflows/mobile-universe.yml
name: Mobile Universe Pipeline
on:
  push:
    branches: [main]
    tags: ['v*']

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci && npm run lint && npm test

  build-ios:
    needs: gate
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with: { ruby-version: '3.2', bundler-cache: true }
      - run: bundle exec fastlane ios beta
        env:
          MATCH_PASSWORD: ${{ secrets.MATCH_PASSWORD }}
          APP_STORE_CONNECT_API_KEY: ${{ secrets.ASC_KEY }}

  build-android:
    needs: gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '17' }
      - run: bundle exec fastlane android beta
        env:
          KEYSTORE_PATH: ${{ secrets.KEYSTORE_PATH }}

  build-rn:
    needs: gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: expo/expo-github-action@v8
        with: { eas-version: latest, token: ${{ secrets.EXPO_TOKEN }} }
      - run: eas build --platform all --non-interactive --profile production

  build-flutter:
    needs: gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with: { flutter-version: '3.24.0' }
      - run: flutter build appbundle --release && flutter build ios --release --no-codesign

  build-pwa:
    needs: gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build:pwa
      - uses: peaceiris/actions-gh-pages@v4
        with: { publish_dir: ./dist, cname: app.example.com }
```

**Integration Points:** MU7 builds artifacts from MU2 (RN), MU3 (Flutter),
MU4 (PWA), and native targets. MU6 test matrix runs inside the pipeline.
MU8 code signing and obfuscation steps execute during build. MU1 core is
compiled/bundled into each target.

---

## MU8: Mobile Security Hardening

**Purpose:** Comprehensive mobile security covering certificate pinning, secure
keychain/keystore storage, biometric authentication, code obfuscation, runtime
integrity checks, and data-at-rest encryption.

**Design Pattern:** *Defense in Depth* — multiple overlapping security layers so
compromise of one does not expose the application.

### Security Layer Stack

```
┌──────────────────────────────────────────┐
│          TRANSPORT SECURITY               │
│  TLS 1.3 · Certificate Pinning · HSTS    │
├──────────────────────────────────────────┤
│          AUTHENTICATION                   │
│  Biometric · MFA · Token Rotation · PKCE  │
├──────────────────────────────────────────┤
│          STORAGE SECURITY                 │
│  Keychain/Keystore · Encrypted SharedPrefs│
│  IndexedDB Encryption · Secure Enclaves   │
├──────────────────────────────────────────┤
│          RUNTIME INTEGRITY                │
│  Jailbreak Detection · Debugger Detection │
│  Root Check · Tamper Detection            │
├──────────────────────────────────────────┤
│          CODE PROTECTION                  │
│  ProGuard/R8 · Hermes Bytecode · Tree     │
│  Shaking · Source Map Protection          │
└──────────────────────────────────────────┘
```

### Certificate Pinning (React Native — TrustKit)

```typescript
// src/security/CertificatePinning.ts
import { Platform } from 'react-native';

export const SSL_PINNING_CONFIG = {
  'api.example.com': {
    includeSubdomains: true,
    expirationDate: '2026-12-31',
    publicKeyHashes: [
      'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=', // primary
      'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=', // backup
    ],
  },
};

export function createPinnedFetch(url: string, options: RequestInit) {
  if (Platform.OS === 'ios') {
    return fetch(url, {
      ...options,
      // @ts-expect-error — custom RN prop for TrustKit
      sslPinning: { certs: ['api_cert'] },
    });
  }
  return fetch(url, options);
}
```

### Secure Storage Adapter (Kotlin — Android Keystore)

```kotlin
// security/SecureStorageAdapter.kt
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecureStorageAdapter(private val context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .setUserAuthenticationRequired(true)
        .setUserAuthenticationParameters(
            300, // 5 min validity
            KeyProperties.AUTH_BIOMETRIC_STRONG or
                KeyProperties.AUTH_DEVICE_CREDENTIAL,
        )
        .build()

    private val prefs = EncryptedSharedPreferences.create(
        context,
        "secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    fun setSecure(key: String, value: String) =
        prefs.edit().putString(key, value).apply()

    fun getSecure(key: String): String? = prefs.getString(key, null)

    fun deleteSecure(key: String) = prefs.edit().remove(key).apply()

    fun clearAll() = prefs.edit().clear().apply()
}
```

### iOS Keychain Wrapper (Swift)

```swift
// Security/KeychainAdapter.swift
import Security
import LocalAuthentication

struct KeychainAdapter {
    static func set(key: String, value: Data,
                    biometric: Bool = false) -> Bool {
        let context = LAContext()
        var query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: value,
            kSecAttrAccessible as String:
                kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
        ]
        if biometric {
            let access = SecAccessControlCreateWithFlags(
                nil,
                kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly,
                .biometryCurrentSet,
                nil
            )!
            query[kSecAttrAccessControl as String] = access
            query[kSecUseAuthenticationContext as String] = context
        }
        SecItemDelete(query as CFDictionary)
        return SecItemAdd(query as CFDictionary, nil) == errSecSuccess
    }

    static func get(key: String) -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var item: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &item) == errSecSuccess
        else { return nil }
        return item as? Data
    }

    static func delete(key: String) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
        ]
        return SecItemDelete(query as CFDictionary) == errSecSuccess
    }
}
```

### Runtime Integrity Check

```typescript
// src/security/IntegrityCheck.ts
import { Platform, NativeModules } from 'react-native';

interface IntegrityResult {
  isRooted: boolean;
  isDebugged: boolean;
  isTampered: boolean;
  isEmulator: boolean;
}

export async function checkIntegrity(): Promise<IntegrityResult> {
  if (Platform.OS === 'android') {
    const result = await NativeModules.IntegrityModule.check();
    return {
      isRooted: result.rooted,
      isDebugged: result.debugged,
      isTampered: result.tampered,
      isEmulator: result.emulator,
    };
  }
  if (Platform.OS === 'ios') {
    const result = await NativeModules.IntegrityModule.check();
    return {
      isRooted: result.jailbroken,
      isDebugged: result.debuggerAttached,
      isTampered: result.signatureInvalid,
      isEmulator: result.simulator,
    };
  }
  // PWA — limited checks
  return {
    isRooted: false,
    isDebugged: typeof window !== 'undefined' && !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__,
    isTampered: false,
    isEmulator: false,
  };
}

export function enforceIntegrity(result: IntegrityResult): void {
  if (result.isRooted || result.isTampered) {
    throw new Error('SECURITY_VIOLATION: Device integrity compromised');
  }
  if (__DEV__ === false && result.isDebugged) {
    throw new Error('SECURITY_VIOLATION: Debugger detected in production');
  }
}
```

**Integration Points:** MU8 wraps all network calls from MU2/MU3/MU4 with cert
pinning. MU1 storage ports are implemented by MU8 secure adapters. MU7 pipeline
runs obfuscation and code signing. MU6 includes security-specific E2E tests.

---

## 🌳 Decision Tree — Module Routing

```
START: What do you need?
│
├── "Write shared business logic" ──────────────→ MU1 (Platform Abstraction Core)
│
├── "Build a React Native screen" ──────────────→ MU2 (React Native Reactor)
│    └── "with native module" ──────────────────→ MU2 + MU8 (security bridge)
│
├── "Build a Flutter screen" ───────────────────→ MU3 (Flutter Fusion Engine)
│    └── "with platform channel" ───────────────→ MU3 + MU8 (secure channel)
│
├── "Build an offline-first web app" ───────────→ MU4 (Progressive Web Synthesis)
│    └── "with background sync" ────────────────→ MU4 + MU7 (deploy to CDN)
│
├── "Design app architecture" ──────────────────→ MU5 (Architecture Patterns)
│    ├── "with MVVM" ───────────────────────────→ MU5 (Kotlin/Swift ViewModel)
│    ├── "with BLoC" ───────────────────────────→ MU5 + MU3 (Flutter BLoC)
│    └── "with Redux" ──────────────────────────→ MU5 + MU2 (RN Redux)
│
├── "Test across platforms" ────────────────────→ MU6 (Testing Matrix)
│    ├── "E2E with Maestro" ────────────────────→ MU6 (cross-platform YAML)
│    ├── "E2E with Detox" ──────────────────────→ MU6 + MU2 (RN-specific)
│    └── "widget tests" ────────────────────────→ MU6 + MU3 (Flutter-specific)
│
├── "Deploy to stores" ─────────────────────────→ MU7 (Deployment Pipeline)
│    ├── "with OTA updates" ────────────────────→ MU7 (CodePush / Shorebird)
│    └── "with code signing" ───────────────────→ MU7 + MU8 (signing + security)
│
├── "Harden security" ──────────────────────────→ MU8 (Security Hardening)
│    ├── "cert pinning" ────────────────────────→ MU8 (TrustKit / NSAppTransport)
│    ├── "biometric auth" ──────────────────────→ MU8 + MU1 (auth use case)
│    └── "secure storage" ──────────────────────→ MU8 (Keychain / Keystore)
│
└── "Generate for ALL platforms at once" ───────→ EMERGENT MODE
     └── Feed feature spec (MU1) through ───────→ MU2 + MU3 + MU4 + Native
         MU5 architecture, tested by MU6,         simultaneously
         deployed by MU7, secured by MU8
```

---

## 🔗 Cross-Module Integration Patterns

### Pattern 1: MU1 Core → MU2 + MU3 + MU4 (Simultaneous Rendering)

The same `AuthenticateUser` use case from MU1 is consumed by three different
platform adapters without modification:

```
MU1: AuthenticateUser (pure business logic)
 ├── MU2: useInjection<AuthenticateUser>()    → React Native hook
 ├── MU3: ref.watch(authenticateUserProvider)  → Flutter Riverpod
 ├── MU4: new AuthenticateUser(adapters...)    → PWA constructor
 ├── iOS: LoginViewModel(authenticateUser)     → SwiftUI @StateObject
 └── And: LoginViewModel(authenticateUser)     → Kotlin StateFlow
```

### Pattern 2: MU6 Testing → All Platform Targets

A single Maestro test specification validates the same user flow across React
Native, Flutter, and native builds. Framework-specific tests (Detox, widget
tests, XCTest) handle platform-unique behaviors.

### Pattern 3: MU7 Pipeline → MU8 Security → Store Submission

```
Code Push → MU7 CI Gate
  → MU8 obfuscation (ProGuard/R8, Hermes bytecode)
  → MU8 cert embedding (pin sets baked into binary)
  → MU7 code signing (match/Fastlane)
  → MU6 E2E test gate
  → MU7 store submission (TestFlight, Play Internal, CDN)
```

### Pattern 4: Emergent — 1 Spec → 5 Platforms

```yaml
# Input: specs/features/user-auth.feature.yaml (MU1 spec)
#
# Pipeline execution:
# 1. MU1 parses the spec → domain model + use case skeleton
# 2. MU5 applies architecture pattern (MVVM for native, hooks for RN, Riverpod for FL)
# 3. MU2 generates LoginScreen.tsx (React Native)
# 4. MU3 generates login_screen.dart (Flutter)
# 5. MU4 generates LoginScreen.ts (PWA Web Component)
# 6. Native: generates LoginView.swift + LoginViewModel.kt
# 7. MU8 wraps all with security (cert pinning, secure storage, biometric)
# 8. MU6 generates test files for each platform from spec assertions
# 9. MU7 builds + signs + deploys all 5 targets in parallel
```

---

## 🌐 Domain Applications

### E-Commerce App
- **MU1:** Product catalog, cart, checkout, payment domain
- **MU2+MU3:** Native mobile shopping experience with gesture-driven UX
- **MU4:** PWA for instant web checkout (no install required)
- **MU7:** Deploy iOS/Android to stores, PWA to CDN, RN via OTA updates
- **MU8:** PCI-DSS compliance, tokenized payments, cert pinning to payment API

### Healthcare / Telehealth
- **MU1:** Patient records, appointment booking, HIPAA-compliant data models
- **MU5:** Strict Clean Architecture for audit trail and testability
- **MU8:** Biometric auth required, encrypted local storage, no data on rooted devices
- **MU6:** Compliance-grade test coverage with automated regression

### Field Service / Offline-First
- **MU4:** PWA with full offline capability via service workers + IndexedDB
- **MU1:** Work order, inspection, and reporting domain logic
- **MU3:** Flutter for ruggedized tablets with custom hardware integration
- **MU7:** OTA updates via Shorebird when field devices reconnect

### Social / Messaging
- **MU2:** React Native for rapid iteration with Reanimated gesture-driven UI
- **MU1:** Message threading, real-time sync, notification domain
- **MU8:** End-to-end encryption, secure key exchange, message retention policies
- **MU6:** Maestro E2E for cross-platform messaging flow validation

---

## 📋 Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════════════╗
║              FORGE-MOBILE-UNIVERSE — QUICK REFERENCE                 ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  MU1  Platform Abstraction Core    TypeScript domain + use cases      ║
║  MU2  React Native Reactor         Expo · bare · Reanimated · TurboM  ║
║  MU3  Flutter Fusion Engine        Dart · Riverpod · GoRouter · Chan  ║
║  MU4  Progressive Web Synthesis    SW · Workbox · offline · manifest  ║
║  MU5  Architecture Patterns        Clean Arch · MVVM · BLoC · Redux   ║
║  MU6  Testing Matrix               Detox · Maestro · Jest · Widget    ║
║  MU7  Deployment Pipeline          Fastlane · EAS · Shorebird · CDN   ║
║  MU8  Security Hardening           Pinning · Keychain · Biometric     ║
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║  EMERGENT CAPABILITY                                                  ║
║  1 Feature Spec → 5 Platform Outputs                                  ║
║  iOS (Swift/SwiftUI) + Android (Kotlin/Compose) + React Native        ║
║  + Flutter + PWA — shared logic, platform UI, unified tests & CI/CD   ║
╠═══════════════════════════════════════════════════════════════════════╣
║  FORGE CLASS: cross-domain-innovation  │  FUSED SKILLS: 8            ║
║  TIER: FORGE (Ω-Δ99)                  │  VERSION: 1.0.0             ║
║  AUTHOR: andrew-pigors + copilot-omega-delta-99                       ║
║  DATE: 2026-03-27                                                     ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

*Forged by Omega-Delta-99 — Universal Platform Transcendence achieved.*
