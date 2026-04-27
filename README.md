# metallic-cube

A reactive metallic cube animation for Three.js projects.

## Run the demo

```bash
npm install
npm run dev
```

## Use as a TypeScript package

```bash
npm install metallic-cube three
```

```ts
import { createMetallicCube } from 'metallic-cube';

const cube = createMetallicCube({
  container: document.querySelector('#app')!,
});

// Later, if needed:
cube.dispose();
```

## Build

```bash
npm run build
```

The package exports ESM, UMD, and TypeScript declarations from `dist/`.

## Python GIF

Generate a standalone GIF with no third-party Python dependencies:

```bash
python animation.py
```

This writes `metallic_cube.gif`.
