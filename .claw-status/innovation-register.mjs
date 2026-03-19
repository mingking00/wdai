import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
const innovationLoaderURL = pathToFileURL('/usr/lib/node_modules/openclaw/innovation-loader.mjs');
register(innovationLoaderURL);
console.error('[Innovation] Bottom-layer loader registered ✅');
