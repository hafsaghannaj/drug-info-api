const fs = require('fs/promises');
const path = require('path');

const root = path.resolve(__dirname, '..');
const webDir = path.join(root, 'www');
const srcFiles = ['index.html', 'styles.css', 'app.js', 'manifest.webmanifest', 'sw.js'];
const srcIcons = path.join(root, 'icons');
const destIcons = path.join(webDir, 'icons');

async function copyFile(src, dest) {
  await fs.mkdir(path.dirname(dest), { recursive: true });
  await fs.copyFile(src, dest);
}

async function copyDir(src, dest) {
  const entries = await fs.readdir(src, { withFileTypes: true });
  await fs.mkdir(dest, { recursive: true });
  await Promise.all(
    entries.map(async (entry) => {
      const from = path.join(src, entry.name);
      const to = path.join(dest, entry.name);
      if (entry.isDirectory()) {
        await copyDir(from, to);
      } else if (entry.isFile()) {
        await copyFile(from, to);
      }
    })
  );
}

async function run() {
  await fs.mkdir(webDir, { recursive: true });
  await Promise.all(
    srcFiles.map((file) => copyFile(path.join(root, file), path.join(webDir, file)))
  );
  try {
    await copyDir(srcIcons, destIcons);
  } catch (err) {
    if (err.code !== 'ENOENT') throw err;
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
