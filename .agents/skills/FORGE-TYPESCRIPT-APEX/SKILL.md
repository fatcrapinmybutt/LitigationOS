---
name: FORGE-TYPESCRIPT-APEX
description: >-
  Full-spectrum TypeScript mastery engine fusing 10 framework and language skills
  into a unified superskill. Achieves Framework Transcendence — the emergent ability
  to write universal TypeScript that auto-adapts to React, Vue, Angular, Svelte, or
  vanilla Web Components. Handles component architecture, SSR/SSG, state management,
  design systems, performance optimization, type-level programming, testing, and
  cross-framework migration as a single coherent discipline.
category: engineering
version: "1.0.0"
triggers:
  - "typescript component"
  - "react to vue migration"
  - "cross-framework"
  - "universal component"
  - "type-safe state"
  - "SSR SSG ISR"
  - "design system tokens"
  - "framework migration"
  - "advanced generics"
  - "bundle optimization"
  - "fullstack typescript"
  - "framework transcendence"
metadata:
  tier: FORGE
  fused_skills: 10
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: domain-mastery
  emergent_capability: >-
    Framework Transcendence — write once in universal TypeScript dialect,
    auto-adapt to ANY framework. Pattern recognition detects which paradigm
    fits the problem best, then generates idiomatic code for the target.
---

# ⚡ FORGE-TYPESCRIPT-APEX
### Universal TypeScript Mastery Engine (Ω-Δ99)

> **Forged from 10 skills. One unified discipline.**
>
> | Attribute  | Value                                                        |
> |------------|--------------------------------------------------------------|
> | **Tier**   | FORGE — Domain Mastery                                       |
> | **Domain** | TypeScript · Frontend Frameworks · Fullstack Engineering      |
> | **Scope**  | React · Next.js · Angular · Vue · Svelte · Node.js · Web APIs|
> | **Emergent**| Framework Transcendence — universal TS → any framework       |
>
> This is not ten skills stapled together. It is the *irreducible synthesis* that
> emerges when component patterns, type theory, rendering strategies, state machines,
> design tokens, and runtime performance fuse into a single cognitive model.
> The whole exceeds the sum of its parts.

---

## 🔥 Forged Skills

| # | Source Skill | Absorbed Capability |
|---|---|---|
| 1 | `react-component-patterns` | Hooks, compound components, render props, HOCs, suspense boundaries |
| 2 | `nextjs-app-builder` | App Router, Server Components, SSR/SSG/ISR, middleware, route handlers |
| 3 | `angular-enterprise` | Dependency injection, RxJS pipelines, signals, NgModules, standalone |
| 4 | `vue-composition-mastery` | Composition API, reactivity system, `<script setup>`, composables |
| 5 | `svelte-kit-builder` | Runes, `$state`/`$derived`, load functions, form actions, streaming |
| 6 | `tailwind-system-design` | Utility-first tokens, theme configuration, plugin authoring, CVA |
| 7 | `typescript-strict-mode` | Conditional types, mapped types, template literals, type-level programming |
| 8 | `nodejs-performance` | Event loop tuning, worker threads, streaming, memory profiling |
| 9 | `state-management-patterns` | Redux Toolkit, Zustand, Pinia, Angular signals, Svelte stores, XState |
| 10 | `web-components-standard` | Custom Elements, Shadow DOM, HTML templates, framework-agnostic interop |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FORGE-TYPESCRIPT-APEX  (Ω-Δ99)                       │
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │   TS1    │──▶│   TS2    │──▶│   TS5    │──▶│   TS6    │            │
│  │Component │   │  Type    │   │ Design   │   │  Perf    │            │
│  │  Forge   │   │ Alchemy  │   │ System   │   │Overdrive │            │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘            │
│       │              │              │              │                    │
│       ▼              ▼              ▼              ▼                    │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │              FRAMEWORK TRANSCENDENCE CORE               │           │
│  │    Universal AST ◆ Pattern Matching ◆ Idiom Mapping     │           │
│  └─────────────────────────────────────────────────────────┘           │
│       ▲              ▲              ▲              ▲                    │
│       │              │              │              │                    │
│  ┌────┴─────┐   ┌────┴─────┐   ┌────┴─────┐   ┌────┴─────┐           │
│  │   TS3    │   │   TS4    │   │   TS7    │   │   TS8    │           │
│  │SSR/SSG   │◀──│  State   │──▶│ Testing  │──▶│Migration │           │
│  │ Reactor  │   │Singularity│   │Continuum │   │ Engine   │           │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘           │
│                                                                         │
│  Data Flow:  TS1→TS2→TS5→TS6  (build path)                            │
│              TS3←TS4→TS7→TS8  (runtime path)                           │
│              All modules feed/read Framework Transcendence Core         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module TS1: Universal Component Forge

**Purpose:** Define components in a framework-neutral intermediate representation,
then compile to idiomatic React, Vue, Angular, Svelte, or Web Component output.

**Design Pattern:** *Adapter + Abstract Factory* — a universal component descriptor
feeds framework-specific renderers that produce native code.

### Universal Component Descriptor

```typescript
// ── Universal Component Definition ──────────────────────────────
interface UniversalComponent<Props extends Record<string, unknown>> {
  name: string;
  props: PropSchema<Props>;
  slots: Record<string, SlotDef>;
  state: StateDescriptor[];
  effects: EffectDescriptor[];
  render: (ctx: RenderContext<Props>) => VNode;
}

type PropSchema<T> = {
  [K in keyof T]: {
    type: PropType<T[K]>;
    required: boolean;
    default?: T[K];
    validator?: (value: T[K]) => boolean;
  };
};

interface SlotDef {
  name: string;
  scope?: Record<string, unknown>;
  fallback?: VNode;
}

interface StateDescriptor {
  key: string;
  initial: unknown;
  derived?: (state: Record<string, unknown>) => unknown;
}

interface EffectDescriptor {
  deps: string[];
  handler: (ctx: EffectContext) => void | (() => void);
  timing: 'mount' | 'update' | 'always';
}
```

### Framework-Specific Compilation

```typescript
// ── React Output ────────────────────────────────────────────────
function compileToReact<P extends Record<string, unknown>>(
  component: UniversalComponent<P>
): React.FC<P> {
  return function ReactAdapter(props: P) {
    const stateMap = new Map<string, [unknown, React.Dispatch<unknown>]>();

    for (const s of component.state) {
      const [val, set] = React.useState(s.initial);
      stateMap.set(s.key, [val, set]);
    }

    for (const effect of component.effects) {
      const deps = effect.deps.map((d) => stateMap.get(d)?.[0]);
      React.useEffect(() => {
        const ctx = buildEffectContext(stateMap, props);
        return effect.handler(ctx) as void | (() => void);
      }, effect.timing === 'always' ? undefined : deps);
    }

    const ctx = buildRenderContext(stateMap, props, component.slots);
    return component.render(ctx) as React.ReactElement;
  };
}

// ── Vue Output ──────────────────────────────────────────────────
function compileToVue<P extends Record<string, unknown>>(
  component: UniversalComponent<P>
): DefineComponent<P> {
  return defineComponent({
    name: component.name,
    props: toVueProps(component.props),
    setup(props, { slots }) {
      const stateRefs = new Map<string, Ref>();

      for (const s of component.state) {
        stateRefs.set(s.key, ref(s.initial));
      }

      for (const derived of component.state.filter((s) => s.derived)) {
        stateRefs.set(
          derived.key,
          computed(() => derived.derived!(refsToPlain(stateRefs)))
        );
      }

      for (const effect of component.effects) {
        const sources = effect.deps.map((d) => stateRefs.get(d)!);
        watchEffect(() => {
          sources.forEach((s) => s.value); // track
          effect.handler(buildEffectContext(stateRefs, props));
        });
      }

      return () => component.render(buildRenderContext(stateRefs, props, slots));
    },
  });
}
```

### Integration Points
- **→ TS2**: Props schema uses Type Alchemy for compile-time validation.
- **→ TS5**: Render context includes design tokens from the Design System Compiler.
- **→ TS8**: Migration Engine uses Universal Component as the intermediate pivot format.

---

## Module TS2: Type Alchemy

**Purpose:** Advanced type-level programming that enforces correctness at compile time
across all framework boundaries. Types become executable specifications.

**Design Pattern:** *Type-Level Interpreter* — conditional types, mapped types, and
template literal types form a compile-time DSL that validates framework contracts.

### Deep Prop Inference

```typescript
// ── Extract prop types from any framework component ─────────────
type ExtractProps<T> =
  T extends React.FC<infer P> ? P :
  T extends DefineComponent<infer P, any, any> ? P :
  T extends { new (): { $props: infer P } } ? P :  // Angular-style
  T extends SvelteComponent<infer P> ? P :
  T extends HTMLElement ? Record<string, unknown> :  // Web Component
  never;

// ── Type-safe event map across frameworks ───────────────────────
type UniversalEventMap<Events extends Record<string, unknown>> = {
  [K in keyof Events as `on${Capitalize<string & K>}`]: (
    payload: Events[K]
  ) => void;
};

// ── Recursive deep partial with path-aware keys ─────────────────
type DeepPartial<T> = T extends object
  ? { [K in keyof T]?: DeepPartial<T[K]> }
  : T;

type PathKeys<T, Prefix extends string = ''> = T extends object
  ? {
      [K in keyof T & string]: K extends string
        ? `${Prefix}${K}` | PathKeys<T[K], `${Prefix}${K}.`>
        : never;
    }[keyof T & string]
  : never;
```

### Branded Types for Domain Safety

```typescript
// ── Prevent string misuse across API boundaries ─────────────────
declare const __brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [__brand]: B };

type UserId = Brand<string, 'UserId'>;
type SessionToken = Brand<string, 'SessionToken'>;
type CSSClassName = Brand<string, 'CSSClassName'>;
type RoutePathname = Brand<string, 'RoutePathname'>;

function createUserId(raw: string): UserId {
  if (!/^usr_[a-z0-9]{16}$/.test(raw)) throw new Error('Invalid user ID');
  return raw as UserId;
}

// Compile-time safety — this fails:
// const tok: SessionToken = createUserId('usr_abc1234567890def');
//                           ~~~ Type 'UserId' is not assignable to 'SessionToken'
```

### Template Literal Route Typing

```typescript
// ── Type-safe route parameters extracted from path strings ──────
type ExtractParams<Path extends string> =
  Path extends `${string}:${infer Param}/${infer Rest}`
    ? { [K in Param]: string } & ExtractParams<`/${Rest}`>
    : Path extends `${string}:${infer Param}`
      ? { [K in Param]: string }
      : {};

type AppRoutes = {
  '/users/:userId': ExtractParams<'/users/:userId'>;
  '/users/:userId/posts/:postId': ExtractParams<'/users/:userId/posts/:postId'>;
};

// Result: { userId: string } and { userId: string; postId: string }
// Works identically in Next.js App Router, SvelteKit, or custom Node router.

function navigate<P extends keyof AppRoutes>(
  path: P,
  params: AppRoutes[P]
): void {
  const url = (path as string).replace(
    /:(\w+)/g,
    (_, key) => (params as Record<string, string>)[key]
  );
  // Framework-agnostic — inject into Next router, Vue router, SvelteKit goto, etc.
  window.history.pushState(null, '', url);
}
```

### Integration Points
- **→ TS1**: Universal Component props validated by recursive type inference.
- **→ TS4**: State Singularity uses branded types for store isolation.
- **→ TS7**: Testing Continuum uses `ExtractProps` for auto-generated test fixtures.

---

## Module TS3: SSR/SSG Reactor

**Purpose:** Unify server rendering strategies (SSR, SSG, ISR, streaming) across
Next.js, Nuxt, and SvelteKit into a single mental model with portable patterns.

**Design Pattern:** *Strategy + Template Method* — a rendering pipeline selects the
correct strategy per route, with framework adapters handling the plumbing.

### Unified Data Loading

```typescript
// ── Framework-agnostic data loader ──────────────────────────────
interface RouteLoader<Data> {
  type: 'static' | 'server' | 'incremental' | 'streaming';
  revalidate?: number;  // seconds (ISR)
  load: (ctx: LoadContext) => Promise<Data> | AsyncGenerator<Data>;
  fallback?: () => Data;
  errorBoundary?: (error: Error) => Data;
}

interface LoadContext {
  params: Record<string, string>;
  searchParams: URLSearchParams;
  headers: Headers;
  cookies: ReadonlyMap<string, string>;
}

// ── Next.js App Router adapter ──────────────────────────────────
function toNextPage<Data>(loader: RouteLoader<Data>) {
  if (loader.type === 'static') {
    return {
      generateStaticParams: async () => [],  // build-time
      default: async ({ params }: { params: Record<string, string> }) => {
        const data = await loader.load({ params } as LoadContext);
        return data;
      },
    };
  }

  if (loader.type === 'incremental') {
    return {
      revalidate: loader.revalidate,
      default: async ({ params }: { params: Record<string, string> }) => {
        return loader.load({ params } as LoadContext);
      },
    };
  }

  // SSR — no caching
  return {
    dynamic: 'force-dynamic' as const,
    default: async ({ params }: { params: Record<string, string> }) => {
      return loader.load({ params } as LoadContext);
    },
  };
}

// ── SvelteKit adapter ───────────────────────────────────────────
function toSvelteKitLoad<Data>(loader: RouteLoader<Data>) {
  return async ({ params, url, request }: SvelteKitLoadEvent) => {
    const ctx: LoadContext = {
      params,
      searchParams: url.searchParams,
      headers: request.headers,
      cookies: new Map(),
    };
    const data = await loader.load(ctx);
    return { data };
  };
}
```

### Streaming SSR Pattern

```typescript
// ── Unified streaming for long-running data fetches ─────────────
async function* streamingLoader(ctx: LoadContext) {
  // Yield shell immediately
  yield { status: 'loading', items: [] };

  // Stream results as they arrive
  const cursor = db.query('SELECT * FROM products WHERE ...').cursor();
  const batch: Product[] = [];

  for await (const row of cursor) {
    batch.push(row);
    if (batch.length >= 20) {
      yield { status: 'streaming', items: [...batch] };
      batch.length = 0;
    }
  }

  yield { status: 'complete', items: batch };
}

// Next.js: use with React Suspense + Server Components
// SvelteKit: use with streaming load + await blocks
// Nuxt: use with useAsyncData + lazy hydration
```

### Integration Points
- **→ TS4**: State Singularity hydrates server-fetched data into client stores.
- **→ TS6**: Performance Overdrive selects optimal chunk boundaries per route.
- **→ TS2**: Route types validated by template literal ExtractParams at compile time.

---

## Module TS4: State Singularity

**Purpose:** Universal state management patterns that transcend framework-specific
libraries. One conceptual model — Redux, Zustand, Pinia, signals, and stores are
just implementation details.

**Design Pattern:** *Mediator + Observer* — a universal store protocol with
framework-specific bindings that maintain reactivity contracts.

### Universal Store Protocol

```typescript
// ── Core protocol — works everywhere ────────────────────────────
interface UniversalStore<State, Actions extends Record<string, (...args: any[]) => void>> {
  getState(): Readonly<State>;
  subscribe(listener: (state: State, prevState: State) => void): () => void;
  actions: Actions;
  select<T>(selector: (state: State) => T): T;
}

type StoreDefinition<State, Actions extends Record<string, (...args: any[]) => void>> = {
  initialState: State;
  actions: (
    set: (updater: Partial<State> | ((prev: State) => Partial<State>)) => void,
    get: () => State
  ) => Actions;
  middleware?: Middleware<State>[];
};

type Middleware<State> = (
  next: (updater: Partial<State>) => void
) => (updater: Partial<State>) => void;

// ── Create a universal store ────────────────────────────────────
function createUniversalStore<
  State extends Record<string, unknown>,
  Actions extends Record<string, (...args: any[]) => void>
>(def: StoreDefinition<State, Actions>): UniversalStore<State, Actions> {
  let state = { ...def.initialState };
  const listeners = new Set<(s: State, p: State) => void>();

  const rawSet = (partial: Partial<State>) => {
    const prev = { ...state };
    Object.assign(state, partial);
    listeners.forEach((fn) => fn({ ...state }, prev));
  };

  const set = (def.middleware ?? []).reduceRight(
    (next, mw) => mw(next),
    rawSet
  );

  const get = () => ({ ...state });

  const actions = def.actions(
    (updater) => {
      const partial = typeof updater === 'function' ? updater(state) : updater;
      set(partial);
    },
    get
  );

  return {
    getState: get,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    actions,
    select: (selector) => selector(state),
  };
}
```

### Framework Bindings

```typescript
// ── React binding (hook) ────────────────────────────────────────
function useStore<State, Actions extends Record<string, (...args: any[]) => void>, T>(
  store: UniversalStore<State, Actions>,
  selector: (state: State) => T
): T {
  const [value, setValue] = React.useState(() => selector(store.getState()));

  React.useEffect(() => {
    return store.subscribe((state) => {
      const next = selector(state);
      setValue((prev) => (Object.is(prev, next) ? prev : next));
    });
  }, [store, selector]);

  return value;
}

// ── Vue binding (composable) ────────────────────────────────────
function useVueStore<State, Actions extends Record<string, (...args: any[]) => void>>(
  store: UniversalStore<State, Actions>
) {
  const state = reactive(store.getState()) as State;
  store.subscribe((next) => Object.assign(state, next));
  return { state: readonly(state), actions: store.actions };
}

// ── Svelte binding (readable store) ─────────────────────────────
function toSvelteStore<State, Actions extends Record<string, (...args: any[]) => void>>(
  store: UniversalStore<State, Actions>
) {
  const { subscribe } = readable(store.getState(), (set) => {
    return store.subscribe((state) => set(state));
  });
  return { subscribe, actions: store.actions };
}

// ── Angular binding (signal) ────────────────────────────────────
function toAngularSignal<State, Actions extends Record<string, (...args: any[]) => void>>(
  store: UniversalStore<State, Actions>
) {
  const sig = signal(store.getState());
  store.subscribe((state) => sig.set(state));
  return { state: sig.asReadonly(), actions: store.actions };
}
```

### Practical Example: Auth Store (All Frameworks)

```typescript
const authStore = createUniversalStore({
  initialState: {
    user: null as User | null,
    token: null as SessionToken | null,  // Branded from TS2
    status: 'idle' as 'idle' | 'loading' | 'authenticated' | 'error',
  },
  actions: (set, get) => ({
    login: async (email: string, password: string) => {
      set({ status: 'loading' });
      try {
        const { user, token } = await api.login(email, password);
        set({ user, token, status: 'authenticated' });
      } catch {
        set({ status: 'error' });
      }
    },
    logout: () => set({ user: null, token: null, status: 'idle' }),
  }),
  middleware: [loggingMiddleware, persistMiddleware('auth')],
});

// React:   const status = useStore(authStore, s => s.status);
// Vue:     const { state } = useVueStore(authStore);  // state.status
// Svelte:  const auth = toSvelteStore(authStore);      // $auth.status
// Angular: const auth = toAngularSignal(authStore);    // auth.state().status
```

### Integration Points
- **→ TS1**: Universal Components bind to stores via framework adapters automatically.
- **→ TS3**: SSR Reactor hydrates stores from server-loaded data.
- **→ TS2**: Branded types (SessionToken) prevent cross-domain state contamination.

---

## Module TS5: Design System Compiler

**Purpose:** Transform design tokens into multi-framework component libraries with
Tailwind integration, ensuring pixel-perfect consistency across React, Vue, Angular,
Svelte, and Web Components.

**Design Pattern:** *Builder + Interpreter* — tokens compile through a pipeline that
generates framework-specific theme providers, component variants, and utility classes.

### Token Definition Layer

```typescript
// ── Design tokens as TypeScript-first source of truth ───────────
const tokens = {
  color: {
    primary:   { 50: '#eff6ff', 500: '#3b82f6', 900: '#1e3a5f' },
    neutral:   { 50: '#fafafa', 500: '#737373', 900: '#171717' },
    semantic: {
      success: '#22c55e',
      warning: '#f59e0b',
      error:   '#ef4444',
      info:    '#3b82f6',
    },
  },
  spacing: {
    xs: '0.25rem', sm: '0.5rem', md: '1rem',
    lg: '1.5rem',  xl: '2rem',  '2xl': '3rem',
  },
  typography: {
    fontFamily: { sans: 'Inter, system-ui, sans-serif', mono: 'JetBrains Mono, monospace' },
    fontSize:   { xs: '0.75rem', sm: '0.875rem', base: '1rem', lg: '1.125rem', xl: '1.25rem' },
    fontWeight: { normal: '400', medium: '500', semibold: '600', bold: '700' },
  },
  radius: { none: '0', sm: '0.25rem', md: '0.375rem', lg: '0.5rem', full: '9999px' },
  shadow: {
    sm: '0 1px 2px rgba(0,0,0,0.05)',
    md: '0 4px 6px rgba(0,0,0,0.1)',
    lg: '0 10px 15px rgba(0,0,0,0.1)',
  },
} as const;

type Tokens = typeof tokens;
type ColorScale = keyof Tokens['color']['primary'];
```

### Component Variant Algebra (CVA Pattern)

```typescript
// ── Class Variance Authority — framework-agnostic variant engine ─
interface VariantConfig<V extends Record<string, Record<string, string>>> {
  base: string;
  variants: V;
  defaultVariants: { [K in keyof V]: keyof V[K] };
  compoundVariants?: Array<
    Partial<{ [K in keyof V]: keyof V[K] }> & { class: string }
  >;
}

function cva<V extends Record<string, Record<string, string>>>(
  config: VariantConfig<V>
) {
  return (props: Partial<{ [K in keyof V]: keyof V[K] }> = {}): string => {
    const resolved = { ...config.defaultVariants, ...props };
    const classes = [config.base];

    for (const [key, value] of Object.entries(resolved)) {
      const variant = config.variants[key as keyof V];
      if (variant) classes.push(variant[value as string]);
    }

    for (const compound of config.compoundVariants ?? []) {
      const { class: cls, ...conditions } = compound;
      const matches = Object.entries(conditions).every(
        ([k, v]) => resolved[k as keyof V] === v
      );
      if (matches) classes.push(cls);
    }

    return classes.filter(Boolean).join(' ');
  };
}

// ── Button variants — consumed by ALL framework adapters ────────
const buttonVariants = cva({
  base: 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50',
  variants: {
    intent:  { primary: 'bg-primary-500 text-white hover:bg-primary-600', secondary: 'bg-neutral-100 text-neutral-900 hover:bg-neutral-200', danger: 'bg-red-500 text-white hover:bg-red-600' },
    size:    { sm: 'h-8 px-3 text-sm', md: 'h-10 px-4 text-base', lg: 'h-12 px-6 text-lg' },
  },
  defaultVariants: { intent: 'primary', size: 'md' },
  compoundVariants: [
    { intent: 'danger', size: 'lg', class: 'uppercase tracking-wide' },
  ],
});
```

### Tailwind Config Generation

```typescript
// ── Auto-generate tailwind.config.ts from tokens ────────────────
function tokensToTailwindConfig(tokens: Tokens): TailwindConfig {
  return {
    theme: {
      extend: {
        colors: {
          primary: tokens.color.primary,
          neutral: tokens.color.neutral,
          ...tokens.color.semantic,
        },
        spacing: tokens.spacing,
        fontFamily: tokens.typography.fontFamily,
        fontSize: tokens.typography.fontSize,
        borderRadius: tokens.radius,
        boxShadow: tokens.shadow,
      },
    },
  };
}
```

### Integration Points
- **→ TS1**: Universal Components receive variant classes from the CVA engine.
- **→ TS2**: Token types validated at compile time via `as const` inference.
- **→ TS6**: Tree-shaking removes unused variant classes from production bundles.

---

## Module TS6: Performance Overdrive

**Purpose:** Optimize TypeScript applications at every level — bundle size, runtime
speed, memory footprint, rendering performance — across all target frameworks.

**Design Pattern:** *Pipeline + Profiler* — a multi-stage optimization pipeline with
measurement hooks at each stage.

### Bundle Analysis & Code Splitting

```typescript
// ── Framework-agnostic lazy loading ─────────────────────────────
type LazyModule<T> = {
  load: () => Promise<{ default: T }>;
  preload: () => void;
  prefetch: () => void;
};

function createLazyModule<T>(loader: () => Promise<{ default: T }>): LazyModule<T> {
  let cached: Promise<{ default: T }> | null = null;

  return {
    load: () => {
      if (!cached) cached = loader();
      return cached;
    },
    preload: () => {
      if (!cached) cached = loader();
    },
    prefetch: () => {
      if (typeof requestIdleCallback !== 'undefined') {
        requestIdleCallback(() => { cached = loader(); });
      }
    },
  };
}

// Usage in any framework's router:
const AdminPanel = createLazyModule(() => import('./admin/AdminPanel'));

// On route hover → AdminPanel.preload()
// On idle       → AdminPanel.prefetch()
// On navigate   → await AdminPanel.load()
```

### Virtual Scrolling Engine

```typescript
// ── High-performance list rendering (10K+ items) ────────────────
interface VirtualListConfig<T> {
  items: T[];
  itemHeight: number | ((index: number) => number);
  overscan: number;
  containerHeight: number;
}

function calculateVisibleRange<T>(
  config: VirtualListConfig<T>,
  scrollTop: number
): { start: number; end: number; offsetY: number } {
  const { items, itemHeight, overscan, containerHeight } = config;
  const getHeight = typeof itemHeight === 'function' ? itemHeight : () => itemHeight;

  let accumulated = 0;
  let start = 0;

  // Find first visible item
  for (let i = 0; i < items.length; i++) {
    const h = getHeight(i);
    if (accumulated + h > scrollTop) { start = i; break; }
    accumulated += h;
  }

  // Find last visible item
  let visible = accumulated;
  let end = start;
  for (let i = start; i < items.length; i++) {
    if (visible > scrollTop + containerHeight) { end = i; break; }
    visible += getHeight(i);
    end = i;
  }

  // Apply overscan
  start = Math.max(0, start - overscan);
  end = Math.min(items.length - 1, end + overscan);

  return { start, end, offsetY: accumulated };
}
```

### Worker Thread Offloading (Node.js)

```typescript
// ── CPU-intensive work off the main thread ──────────────────────
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';

interface WorkerTask<Input, Output> {
  execute: (input: Input) => Promise<Output>;
  pool: (concurrency: number) => WorkerPool<Input, Output>;
}

class WorkerPool<Input, Output> {
  private workers: Worker[] = [];
  private queue: Array<{ input: Input; resolve: (v: Output) => void }> = [];
  private idle: Worker[] = [];

  constructor(private scriptPath: string, concurrency: number) {
    for (let i = 0; i < concurrency; i++) {
      const w = new Worker(scriptPath);
      w.on('message', (result: Output) => {
        const next = this.queue.shift();
        if (next) {
          w.postMessage(next.input);
          // resolve previous
        } else {
          this.idle.push(w);
        }
      });
      this.idle.push(w);
    }
  }

  async run(input: Input): Promise<Output> {
    return new Promise((resolve) => {
      const worker = this.idle.pop();
      if (worker) {
        worker.postMessage(input);
        worker.once('message', resolve);
      } else {
        this.queue.push({ input, resolve });
      }
    });
  }

  terminate(): void {
    this.workers.forEach((w) => w.terminate());
  }
}
```

### Integration Points
- **→ TS3**: SSR Reactor uses streaming + chunk splitting for optimal TTFB.
- **→ TS5**: Tree-shaking removes unused design tokens and variant branches.
- **→ TS1**: Components use lazy loading via the `LazyModule` primitive.

---

## Module TS7: Testing Continuum

**Purpose:** Unified testing strategy spanning unit → integration → e2e across all
frameworks, with shared test utilities and auto-generated fixtures from types.

**Design Pattern:** *Template Method + Factory* — a universal test harness with
framework-specific rendering adapters.

### Universal Test Harness

```typescript
// ── Framework-agnostic component testing ────────────────────────
interface TestHarness<Component, RenderResult> {
  render(component: Component, props?: Record<string, unknown>): RenderResult;
  fireEvent: EventSimulator;
  waitFor: (assertion: () => void, timeout?: number) => Promise<void>;
  cleanup: () => void;
}

interface EventSimulator {
  click(element: Element): Promise<void>;
  type(element: Element, text: string): Promise<void>;
  keyboard(key: string): Promise<void>;
}

// ── React harness (wraps @testing-library/react) ────────────────
function createReactHarness(): TestHarness<React.ReactElement, RenderResult> {
  return {
    render: (el, props) => rtlRender(React.cloneElement(el, props)),
    fireEvent: {
      click: async (el) => { await userEvent.click(el); },
      type: async (el, text) => { await userEvent.type(el, text); },
      keyboard: async (key) => { await userEvent.keyboard(key); },
    },
    waitFor: rtlWaitFor,
    cleanup: rtlCleanup,
  };
}

// ── Vue harness (wraps @vue/test-utils) ─────────────────────────
function createVueHarness(): TestHarness<DefineComponent, VueWrapper> {
  return {
    render: (component, props) => mount(component, { props }),
    fireEvent: {
      click: async (el) => { await (el as any).trigger('click'); },
      type: async (el, text) => { await (el as any).setValue(text); },
      keyboard: async (key) => { await (el as any).trigger('keydown', { key }); },
    },
    waitFor: async (fn, timeout = 1000) => {
      const start = Date.now();
      while (Date.now() - start < timeout) {
        try { fn(); return; } catch { await new Promise((r) => setTimeout(r, 50)); }
      }
      fn();
    },
    cleanup: () => {},
  };
}
```

### Auto-Generated Test Fixtures from Types

```typescript
// ── Generate mock data from TypeScript types ────────────────────
type MockFactory<T> = {
  [K in keyof T]: T[K] extends string
    ? () => string
    : T[K] extends number
      ? () => number
      : T[K] extends boolean
        ? () => boolean
        : T[K] extends Array<infer U>
          ? (count?: number) => U[]
          : T[K] extends object
            ? MockFactory<T[K]>
            : () => T[K];
};

function createMockFactory<T extends Record<string, unknown>>(
  schema: { [K in keyof T]: 'string' | 'number' | 'boolean' | 'array' | Record<string, unknown> }
): () => T {
  return () => {
    const result: Record<string, unknown> = {};
    for (const [key, type] of Object.entries(schema)) {
      if (type === 'string') result[key] = `mock_${key}_${Math.random().toString(36).slice(2, 8)}`;
      else if (type === 'number') result[key] = Math.floor(Math.random() * 1000);
      else if (type === 'boolean') result[key] = Math.random() > 0.5;
    }
    return result as T;
  };
}

// Usage: const mockUser = createMockFactory<User>({ name: 'string', age: 'number', active: 'boolean' });
// const user = mockUser(); // { name: 'mock_name_x7f2k9', age: 342, active: true }
```

### Integration Test Pattern (API + Component)

```typescript
// ── Full-stack integration test pattern ─────────────────────────
describe('UserProfile integration', () => {
  const harness = createReactHarness();
  const mockServer = setupMockServer([
    rest.get('/api/users/:id', (req, res, ctx) =>
      res(ctx.json({ id: req.params.id, name: 'Test User', role: 'admin' }))
    ),
  ]);

  beforeAll(() => mockServer.listen());
  afterEach(() => { mockServer.resetHandlers(); harness.cleanup(); });
  afterAll(() => mockServer.close());

  it('displays user data after fetch completes', async () => {
    const { getByText } = harness.render(<UserProfile userId="usr_001" />);
    await harness.waitFor(() => {
      expect(getByText('Test User')).toBeInTheDocument();
      expect(getByText('admin')).toBeInTheDocument();
    });
  });
});
```

### Integration Points
- **→ TS2**: `ExtractProps<Component>` auto-generates prop fixtures from types.
- **→ TS4**: Store tests use the universal store protocol directly (no framework needed).
- **→ TS8**: Migration Engine validates output via cross-framework test equivalence.

---

## Module TS8: Migration Engine

**Purpose:** Automated cross-framework migration — convert React↔Vue↔Angular↔Svelte
codebases with high fidelity. The culmination of Framework Transcendence.

**Design Pattern:** *Visitor + Transformer* — parse source framework AST, visit each
node, transform to universal IR, then emit target framework code.

### Migration Pipeline

```typescript
// ── Three-phase migration: Parse → Transform → Emit ─────────────
interface MigrationPipeline<Source, Target> {
  parse(source: string): SourceAST<Source>;
  transform(ast: SourceAST<Source>): UniversalIR;
  emit(ir: UniversalIR): TargetCode<Target>;
  validate(original: string, migrated: string): ValidationReport;
}

interface UniversalIR {
  components: IRComponent[];
  stores: IRStore[];
  routes: IRRoute[];
  styles: IRStyleSheet[];
  tests: IRTestSuite[];
}

interface IRComponent {
  name: string;
  props: IRProp[];
  state: IRState[];
  computed: IRComputed[];
  effects: IREffect[];
  methods: IRMethod[];
  template: IRTemplate;
  slots: IRSlot[];
}

type IRTemplate =
  | { type: 'element'; tag: string; attrs: IRAttr[]; children: IRTemplate[] }
  | { type: 'text'; value: string }
  | { type: 'expression'; code: string }
  | { type: 'conditional'; test: string; consequent: IRTemplate; alternate?: IRTemplate }
  | { type: 'loop'; iterable: string; variable: string; body: IRTemplate };
```

### Concrete Migration: React → Vue 3

```typescript
// ── React hook → Vue composable transformation rules ────────────
const reactToVueRules: TransformRule[] = [
  {
    match: (node) => node.type === 'hook' && node.name === 'useState',
    transform: (node) => ({
      type: 'composable',
      code: `const ${node.variable} = ref(${node.initialValue})`,
      imports: [{ from: 'vue', names: ['ref'] }],
    }),
  },
  {
    match: (node) => node.type === 'hook' && node.name === 'useEffect',
    transform: (node) => ({
      type: 'composable',
      code: node.deps.length === 0
        ? `onMounted(() => { ${node.body} })`
        : `watch([${node.deps.map((d: string) => d).join(', ')}], () => { ${node.body} })`,
      imports: [{ from: 'vue', names: node.deps.length === 0 ? ['onMounted'] : ['watch'] }],
    }),
  },
  {
    match: (node) => node.type === 'hook' && node.name === 'useMemo',
    transform: (node) => ({
      type: 'composable',
      code: `const ${node.variable} = computed(() => ${node.factory})`,
      imports: [{ from: 'vue', names: ['computed'] }],
    }),
  },
  {
    match: (node) => node.type === 'jsx_element',
    transform: (node) => ({
      type: 'template_element',
      tag: node.tag,
      directives: convertJSXPropsToVueDirectives(node.props),
      children: node.children,
    }),
  },
];

function convertJSXPropsToVueDirectives(
  props: JSXProp[]
): VueDirective[] {
  return props.map((prop) => {
    if (prop.name === 'className') return { name: 'class', value: prop.value };
    if (prop.name === 'onClick') return { name: '@click', value: prop.value };
    if (prop.name.startsWith('on')) {
      const event = prop.name.slice(2).toLowerCase();
      return { name: `@${event}`, value: prop.value };
    }
    if (prop.dynamic) return { name: `:${prop.name}`, value: prop.value };
    return { name: prop.name, value: prop.value };
  });
}
```

### Migration Validation

```typescript
// ── Verify migration correctness via behavioral equivalence ─────
interface ValidationReport {
  structuralMatch: number;    // 0-100: AST similarity score
  propsPreserved: boolean;    // All prop interfaces match
  statePreserved: boolean;    // All state shapes match
  eventsPreserved: boolean;   // All event handlers preserved
  renderEquivalent: boolean;  // Visual snapshot match
  testsPassing: boolean;      // Original tests adapted and passing
  issues: MigrationIssue[];
}

interface MigrationIssue {
  severity: 'error' | 'warning' | 'info';
  location: { file: string; line: number };
  message: string;
  suggestion: string;
}

async function validateMigration(
  originalDir: string,
  migratedDir: string,
  sourceFramework: Framework,
  targetFramework: Framework
): Promise<ValidationReport> {
  const originalAST = await parseProject(originalDir, sourceFramework);
  const migratedAST = await parseProject(migratedDir, targetFramework);

  return {
    structuralMatch: computeASTSimilarity(originalAST, migratedAST),
    propsPreserved: compareInterfaces(originalAST.props, migratedAST.props),
    statePreserved: compareStateShapes(originalAST.state, migratedAST.state),
    eventsPreserved: compareEventMaps(originalAST.events, migratedAST.events),
    renderEquivalent: await compareSnapshots(originalDir, migratedDir),
    testsPassing: await runAdaptedTests(migratedDir, targetFramework),
    issues: collectIssues(originalAST, migratedAST),
  };
}
```

### Integration Points
- **→ TS1**: Universal Component IR is the pivot format for all migrations.
- **→ TS7**: Test Continuum validates that migrated code passes equivalent tests.
- **→ TS4**: State stores migrate via the universal store protocol (zero rewrite needed).
- **→ TS5**: Design tokens remain unchanged; only component bindings transform.

---

## 🌳 Decision Tree

```
User Request Arrives
│
├─ "Create a component"
│  ├─ Single framework specified? ──→ TS1 (framework-specific fast path)
│  └─ Multi-framework / universal? ──→ TS1 → TS2 (typed props) → TS5 (styled)
│
├─ "Add type safety"
│  ├─ Prop/API types? ──→ TS2 (branded types, deep inference)
│  └─ Route/state types? ──→ TS2 → TS4 (typed stores) or TS3 (typed routes)
│
├─ "Build a page / route"
│  ├─ Static content? ──→ TS3 (SSG path)
│  ├─ Dynamic data? ──→ TS3 (SSR/ISR) → TS4 (state hydration)
│  └─ Real-time? ──→ TS3 (streaming) → TS4 (subscription store)
│
├─ "Manage state"
│  ├─ Single component? ──→ TS1 (local state)
│  ├─ Cross-component? ──→ TS4 (universal store + framework binding)
│  └─ Cross-framework? ──→ TS4 (universal protocol, no framework lock-in)
│
├─ "Design system / styling"
│  ├─ Token definition? ──→ TS5 (token layer)
│  ├─ Component variants? ──→ TS5 (CVA) → TS1 (bind to components)
│  └─ Tailwind config? ──→ TS5 (auto-generate from tokens)
│
├─ "Optimize performance"
│  ├─ Bundle size? ──→ TS6 (splitting + tree-shaking)
│  ├─ Rendering? ──→ TS6 (virtual scroll, memoization)
│  └─ Server/Node.js? ──→ TS6 (worker pools, streaming)
│
├─ "Write tests"
│  ├─ Unit tests? ──→ TS7 (universal harness + mock factory)
│  ├─ Integration? ──→ TS7 (API mock + component harness)
│  └─ Cross-framework? ──→ TS7 → TS8 (test equivalence validation)
│
└─ "Migrate framework"
   ├─ React → Vue? ──→ TS8 (parse→transform→emit)
   ├─ Vue → Svelte? ──→ TS8 (same pipeline, different rules)
   └─ Any → Any? ──→ TS8 (all paths via Universal IR)
```

---

## 🔗 Cross-Module Integration Patterns

### Cascade 1: Full-Stack Feature Development

```
TS2 (define types) → TS1 (build component) → TS5 (style it)
    → TS4 (wire state) → TS3 (add SSR) → TS6 (optimize) → TS7 (test)
```

**Scenario:** Build a product listing page with filters.

1. **TS2** defines `Product`, `FilterState`, route params types
2. **TS1** creates `<ProductCard>` and `<FilterPanel>` as universal components
3. **TS5** applies design tokens: card shadows, filter chip variants
4. **TS4** creates `filterStore` with universal protocol
5. **TS3** wraps in ISR route loader (revalidate: 60)
6. **TS6** adds virtual scrolling for 10K products, lazy images
7. **TS7** tests: unit (filter logic), integration (API mock), e2e (filter→results)

### Cascade 2: Design System Distribution

```
TS5 (tokens) → TS2 (type-safe tokens) → TS1 (universal components)
    → TS8 (emit per-framework packages) → TS7 (cross-framework test suite)
```

**Scenario:** Ship a design system that works in React, Vue, and Angular.

1. **TS5** defines tokens and CVA variants for 30 components
2. **TS2** generates strict types: `ButtonProps`, `InputProps` per framework
3. **TS1** builds universal component descriptors
4. **TS8** emits `@mylib/react`, `@mylib/vue`, `@mylib/angular` packages
5. **TS7** runs identical test suites across all three outputs

### Cascade 3: Legacy Migration

```
TS8 (analyze source) → TS2 (infer types) → TS1 (universal IR)
    → TS4 (migrate state) → TS5 (preserve styles) → TS7 (validate)
```

**Scenario:** Migrate Angular 14 app to React 19 + Next.js.

1. **TS8** parses Angular templates, services, and modules
2. **TS2** infers TypeScript interfaces from existing code
3. **TS1** converts to universal component descriptors
4. **TS4** transforms RxJS services → Zustand stores via universal protocol
5. **TS5** preserves SCSS → Tailwind utility mapping
6. **TS7** behavioral equivalence test suite validates parity

### Cascade 4: Performance Audit & Remediation

```
TS6 (profile) → TS1 (refactor components) → TS4 (optimize state)
    → TS3 (tune SSR strategy) → TS7 (regression test) → TS6 (re-profile)
```

**Scenario:** React app has 4s TTI; target is under 1.5s.

1. **TS6** profiles: identifies 800KB bundle, unnecessary re-renders, no code-splitting
2. **TS1** refactors monolithic page into lazy-loaded compound components
3. **TS4** replaces prop drilling with selective store subscriptions
4. **TS3** converts appropriate routes from SSR → ISR (cache hits)
5. **TS7** runs performance regression tests (Lighthouse CI)
6. **TS6** re-profiles: validates TTI < 1.5s

---

## 🏢 Domain Applications

### E-Commerce Platform

| Module | Application |
|--------|-------------|
| TS1 | Product cards, checkout flow as universal components |
| TS3 | Product pages: ISR (revalidate: 300). Cart: SSR. Landing: SSG |
| TS4 | Cart store (universal) — works in React storefront + Vue admin |
| TS5 | Brand tokens → Tailwind theme → consistent across apps |
| TS6 | Virtual scroll for catalogs, image lazy loading, edge caching |

### SaaS Dashboard

| Module | Application |
|--------|-------------|
| TS2 | Branded IDs for TenantId, ApiKey, MetricName (domain safety) |
| TS4 | Real-time metric store with WebSocket subscription middleware |
| TS6 | Worker threads for server-side data aggregation |
| TS7 | Integration tests: mock WebSocket → validate chart rendering |
| TS8 | White-label: same dashboard ships as React or Angular per client |

### Design System Company

| Module | Application |
|--------|-------------|
| TS5 | Token-first: clients provide tokens, system compiles components |
| TS1 | 50+ universal components → compiled to React, Vue, Angular, WC |
| TS8 | CI/CD: one source → four npm packages, auto-published on merge |
| TS7 | Visual regression + behavioral tests across all four outputs |
| TS2 | Strict prop contracts ensure type safety in all consumers |

### Microservices Gateway (Node.js)

| Module | Application |
|--------|-------------|
| TS6 | Worker pool for CPU-heavy request transformations |
| TS2 | Branded types for ServiceId, TraceId, CorrelationId across services |
| TS3 | Edge SSR for personalized landing pages, streaming for dashboards |
| TS4 | Distributed cache store with invalidation middleware |
| TS7 | Contract tests: validate API schemas across 20+ microservices |

---

## 📋 Quick Reference Card

```
┌──────────────────────────────────────────────────────────────────┐
│                FORGE-TYPESCRIPT-APEX  Quick Reference             │
│                         (Ω-Δ99)                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TS1  Universal Component Forge   Build once → render anywhere   │
│  TS2  Type Alchemy                Compile-time safety at scale   │
│  TS3  SSR/SSG Reactor             Unified rendering strategies   │
│  TS4  State Singularity           One store protocol, all FWs    │
│  TS5  Design System Compiler      Tokens → themed components     │
│  TS6  Performance Overdrive       Bundle, runtime, server perf   │
│  TS7  Testing Continuum           Unit → integration → e2e       │
│  TS8  Migration Engine            Any framework → any framework  │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  EMERGENT CAPABILITY                                             │
│  Framework Transcendence: Write universal TS, auto-adapt to      │
│  React/Vue/Angular/Svelte. Cross-framework migration becomes     │
│  a compilation step, not a rewrite.                              │
├──────────────────────────────────────────────────────────────────┤
│  KEY TRIGGERS                                                    │
│  "typescript component" · "cross-framework" · "migrate react"    │
│  "universal component" · "type-safe state" · "SSR SSG ISR"       │
│  "design system tokens" · "bundle optimization" · "fullstack ts" │
├──────────────────────────────────────────────────────────────────┤
│  COMMON CASCADES                                                 │
│  Feature:   TS2→TS1→TS5→TS4→TS3→TS6→TS7                        │
│  DesignSys: TS5→TS2→TS1→TS8→TS7                                 │
│  Migration: TS8→TS2→TS1→TS4→TS5→TS7                             │
│  PerfAudit: TS6→TS1→TS4→TS3→TS7→TS6                             │
├──────────────────────────────────────────────────────────────────┤
│  FORGE STATS                                                     │
│  Skills Fused: 10    Modules: 8    Tier: FORGE Domain-Mastery    │
│  Author: andrew-pigors + copilot-omega-delta-99                  │
│  Forged: 2026-03-27  Version: 1.0.0                             │
└──────────────────────────────────────────────────────────────────┘
```

---

*Forged by Ω-Δ99. Ten skills enter. One engine emerges.*
