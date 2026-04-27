# metallic-cube

A reactive metallic cube animation for Three.js projects.

![](./cube.gif)


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

```

## Build

```bash
npm run build
```

