import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const assetsDir = path.join(__dirname, 'dist', 'assets');

if (fs.existsSync(assetsDir)) {
  const files = fs.readdirSync(assetsDir);
  const jsFiles = files.filter(f => f.startsWith('index-') && f.endsWith('.js'));
  const cssFiles = files.filter(f => f.startsWith('index-') && f.endsWith('.css'));

  const primaryJs = jsFiles.find(f => f !== 'index-Dspn5MKl.js' && f !== 'index-1w7WZUhv.js') || jsFiles[0];
  const primaryCss = cssFiles.find(f => f !== 'index-DbMWjMyA.css' && f !== 'index-BtKS39qO.css') || cssFiles[0];

  if (primaryJs) {
    fs.copyFileSync(path.join(assetsDir, primaryJs), path.join(assetsDir, 'index-Dspn5MKl.js'));
    fs.copyFileSync(path.join(assetsDir, primaryJs), path.join(assetsDir, 'index-1w7WZUhv.js'));
    console.log(`Legacy JS aliases created from ${primaryJs}`);
  }

  if (primaryCss) {
    fs.copyFileSync(path.join(assetsDir, primaryCss), path.join(assetsDir, 'index-DbMWjMyA.css'));
    fs.copyFileSync(path.join(assetsDir, primaryCss), path.join(assetsDir, 'index-BtKS39qO.css'));
    console.log(`Legacy CSS aliases created from ${primaryCss}`);
  }
}
