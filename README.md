# metallic-cube

a reactive metal cube component 

![](./cube.gif)


## Run the demo

```bash
bun install
bun run dev
```

## Use as a TypeScript package

```bash
bun install metallic-cube three
```

```ts
import { createMetallicCube } from 'metallic-cube';

const cube = createMetallicCube({
  container: document.querySelector('#app')!,
});

```

## Build

```bash
bun run build
```

