## ME, PROBABLY

🐳 Imitation → learning → combination → accidentally building infrastructure

☕ Chief AI Orchestrator & Web Infra

🕶️ Addicted to Codex & Claude. Still responsible for whatever they confidently invent.

❤️ Health comes first. Get a good night's sleep. The bugs will still be there tomorrow.

## CURRENT SEASON: ONE-PERSON SOFTWARE STUDIO

I build small personal products with AI, then notice that they all need auth, APIs, deployment, versioning, shared components, and somewhere to live.

So naturally I started building those too.

Most of the current work lives in [`yuxino-labs`](https://github.com/yuxino-labs): part product studio, part infrastructure department, part evidence that naming things is easier than finishing them.

### THE FACTORY

- **`meow`** *(private)* — A control plane for my web projects: create a project, trigger GitHub Actions, publish versioned builds to OSS, switch the active version, inject runtime scripts, and delete everything when optimism expires.
- **`meow-api` / `meow-release` / `meow-bootstrap`** *(private)* — The API, centralized release workflow, and bootstrap layer behind `meow`. I wanted to deploy a small app and somehow ended up implementing a small platform team.
- **`web-template` / `server-template` / `web-shared` / `auth`** — Reusable foundations for the next project, because copying the previous project manually stopped feeling artisanal.
- **`home` / `index` / `404`** *(private)* — The front doors, directory, and inevitable destination of the ecosystem.
- **`talk`** *(private)* — A Slidev deck explaining `meow`, presumably in case future me asks why any of this exists.

### PRODUCTS CURRENTLY ALIVE

- **2026–now · `mimi`** *(private)* — Live translated subtitles for macOS. Four words in the README; considerably more words spoken into the microphone.
- **2026 · `nichijou`** *(private)* — A personal daily-life journal with posts, memories, categories, image uploads, comments, search, focus tools, badges, and mobile interactions. It also has enough image-display architecture to suggest I take screenshots very seriously.
- **2026 · `yomi`** *(private)* — A visual workflow editor with React Flow, configurable nodes, branching, execution logs, local persistence, runtime settings, and the dangerous implication that workflows should be understandable.
- **2026 · `paw`** *(private)* — A browser-based file explorer connected to the same release platform. Because files were apparently not sufficiently browsed already.
- **2026 · `ele`** *(private)* — A Chinese meal photo diary for recording what I ate, what I photographed, and how many stars the meal deserved. Michelin, but stored in my own database.
- **2025–2026 · `comet`** *(private)* — A personal board-style web app. It began as an app and eventually caused the surrounding release infrastructure to exist. Classic scope control.
- **2025 · `x` / `x-server`** *(private)* — A mobile expense tracker with quick entry, categories, statistics, and local persistence. The repository is called `x`, which saves valuable time previously wasted on searchable names.

### SIDE QUESTS THAT WERE ACTUALLY QUITE SERIOUS

- **2026 · `deepsuck`** *(private)* — A mobile UI for controlling local Claude Code from my phone through Next.js, SSE, the Claude Agent SDK, and an FRP tunnel via Aliyun. In practical terms: full shell access from bed, protected by one bearer token and good judgment.
- **2026 · `tick`** *(private)* — A Tauri app for managing macOS `launchd` jobs: schedules, scripts, plist previews, stdout/stderr logs, and second-level timing via wrapper scripts. It has Miku in the menu bar because system administration benefits from morale.
- **2026 · `moe`** *(private)* — A local-first mobile expense tracker with charts and a PWA build. Apparently one expense tracker was not enough to understand money.
- **2026 · `wnacg`** *(private)* — A Tauri desktop reader with themes, preloading, and fallback mirrors. Distributed systems, but for reading quietly.
- **2024–2026 · `ashita`** *(private)* — A personal timeline and documentation space built on Nextra. The README still thinks it is a template; the commit history knows better.

## PREVIOUS SEASONS

Things I built, learned from, occasionally shipped, and eventually placed somewhere between “archive” and “character development.”

### THE VUE YEARS

- **2016–2017 · [vido](https://github.com/yuxino/vido)** — A custom video player built with Vue 1.x, when both Vue and I were younger.
- **2017–2019 · [2048](https://github.com/yuxino/2048)** — A Vue version of 2048. The tiles combined more reliably than my project plans.
- **2017–2019 · [WeChat](https://github.com/yuxino/WeChat)** — A WeChat-style client built mostly to learn frontend engineering by recreating an application used by roughly everyone.
- **2017–2018 · [dashboard](https://github.com/yuxino/dashboard)** — Components, interactions, charts, and the early realization that every developer eventually builds a dashboard.
- **2017 · [vue-typescript-starter](https://github.com/yuxino/vue-typescript-starter)** — Vue met TypeScript. They are still together.
- **2019–2020 · `vue-ssr`** *(private)* — An attempt to understand Vue SSR by rebuilding the important parts instead of reading one more article.

### “I CAN PROBABLY IMPLEMENT THAT”

- **2019 · [ob](https://github.com/yuxino/ob)** — An Observer exercise that slowly became a tiny MVVM implementation. Scope creep, but educational.
- **2021 · `react-mini`** *(private)* — A tiny React implementation. Getting `useState` to work was the entire hero's journey.
- **2021 · `react-impl`** *(private)* — I planned to implement React again. This time the repository implemented emptiness.
- **2019 · `react-hook-hoc`** *(private)* — Recreating hooks with HOCs. `useEffect` never finished, perhaps due to a missing dependency.
- **2022 · `promise_impl`** *(private)* — An intended Promise/A+ implementation. The promise remains pending.
- **2020 · `babel-ruby-like-conditional-assignment`** *(private)* — A Babel experiment for Ruby-style conditional assignment. JavaScript briefly wore a fake moustache.
- **2020 · `y-language`** *(private)* — A small language project for learning lexing and parsing. Naming the language was the easiest compiler phase.
- **2017 · `Marisa`** *(private)* — A Java web server built to understand routers, annotations, and thread pools. Framework confidence through framework reimplementation.

### DESKTOP APPS, BEFORE EVERYTHING BECAME A WEB APP AGAIN

- **2019–2020 · [viva](https://github.com/yuxino/viva)** — A desktop Markdown editor built with Electron.
- **2020 · [vscode-pdf-reader](https://github.com/yuxino/vscode-pdf-reader)** — An unpublished VS Code PDF reader. It used pdf.js to fix a pdf.js problem, which went about as well as expected.
- **2020 · [mobile-pdf-viewer](https://github.com/yuxino/mobile-pdf-viewer)** — A modified pdf.js viewer for opening PDFs inside Android WeChat. Same library, different battlefield.
- **2023 · `threejs_cube`** *(private)* — My first Three.js lesson. There was a cube, so I think it worked.

### MOBILE DETOURS

- **2019 · [osu](https://github.com/yuxino/osu)** — A Flutter currency converter made while learning Flutter. The exchange rate changed faster than the project.
- **2020 · [flutter_npass](https://github.com/yuxino/flutter_npass)** — A Flutter client for my unfinished password manager.
- **2020 · `swiftui-npass`** *(private)* — A planned SwiftUI client for the same unfinished password manager. Cross-platform incompletion achieved.
- **2020 · `flutter_juejin`** *(private)* — A Juejin client built while learning Flutter.
- **2023 · `moment`** *(private)* — A Taro mini-app that never got beyond its first page. A very small moment.

### TOOLS I NEEDED ONCE, THEN APPARENTLY FOREVER

- **2017–2019 · [pyfl](https://github.com/yuxino/pyfl)** — Get the first letters of Chinese pinyin in the browser. Bigger than necessary, but functional, which is a recurring architectural theme.
- **2018 · [react-scratch](https://github.com/yuxino/react-scratch)** — A scratch-card component for React. No prizes were harmed.
- **2019–2020 · [lemuro](https://github.com/yuxino/lemuro)** — Filesystem helpers I kept rewriting, promoted into their own package so I could rewrite them centrally.
- **2020 · [the-scripts](https://github.com/yuxino/the-scripts)** — A tiny CLI for browsing and running scripts from `package.json`.
- **2019–2020 · `snippet`** *(private)* — React, TypeScript, SCSS, and Taro snippets saved before AI made remembering syntax optional.
- **2019 · `nirvana`** *(private)* — A home for small web tools. It ended up containing one VS Code snippet helper, achieving a very modest form of nirvana.
- **2020 · `mobile-preview`** *(private)* — Preview a website inside a phone frame. The phone was fake; the CSS problems were real.
- **2020 · `now-serverless`** *(private)* — A serverless proxy returning random Pixiv images. Infrastructure with a clear business purpose.

### LEARNING IN PUBLIC, OR AT LEAST IN GIT

- **2018–2019 · [sicp-ex](https://github.com/yuxino/sicp-ex)** — SICP exercises in Racket. I made it to 2.29, which is either progress or a coordinate.
- **2019–2024 · `algs-notes`** *(private)* — Algorithm notes I occasionally returned to clean up, proving documentation can outlive motivation.
- **2019 · `algs4-ts`** *(private)* — Algorithms, 4th Edition, in TypeScript. It stopped at the README, before asymptotic complexity became measurable.
- **2020 · `source`** *(private)* — A repository for source-code reading notes. I never wrote the notes, but the directory structure was contemplative.
- **2017–2020 · `blog`** *(private)* — Notes, timelines, and several attempts to become someone who maintains a blog.
- **2018–2021 · `meteorite`** *(private)* — A personal blog using GitHub Issues as a CMS. It survived long enough to become geology.
- **2017–2018 · `resume`** *(private)* — My old resume built as a React app, because plain paper lacked a build step.

### SMALL SYSTEMS, LARGE NAMES, AND OTHER RELICS

- **2019 · `task-daily`** *(private)* — A task tracker built with Svelte, Nest, and Docker. Managing tasks required three ecosystems.
- **2019 · `alice`** *(private)* — A Nest backend with counters, notes, and reciprocals: the essential pillars of modern SaaS.
- **2017 · `miaohu`** *(private, archived)* — A Q&A backend. I tried to refactor it, gave up, and began rewriting it instead. An authentic software lifecycle.
- **2019 · `vbot`** *(private)* — A Telegram bot with two commits: `init` and `test`. A complete narrative arc.
- **2020 · `server-npass`** *(private)* — Backend for the password manager. Its README was copied from another project and never recovered its identity.
- **2020 · `urban_transportation_system`** *(private)* — An empty repository with a metropolitan name. Urban planning remains difficult.
- **2020 · `-`** *(private)* — A repository literally named `-`. Its README repeats the same tired sentence nine times. Minimalism peaked here.
- **2020 · `ghost`** *(private)* — Empty repository. Excellent thematic consistency.
- **2023 · `slide`** *(private)* — Empty repository for something called slide. The idea slid away.

## THE PATTERN

I used to build projects to understand technologies.

Now I use technologies—and several AI agents—to build products, then build the system that builds the products.

This may be progress. It may also be a more organized form of the same problem.