#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const projectName = process.argv[2];

if (!projectName) {
  console.error("❌ Please provide a project name:");
  console.error("   npx @maiaframework/create-maia-dashboard my-dashboard");
  process.exit(1);
}

const root = path.resolve(process.cwd(), projectName);
const templateDir = path.join(__dirname, "../templates/default");

console.log(`🚀 Creating project in ${root}...`);
fs.mkdirSync(root, { recursive: true });

function copyRecursive(src, dest) {
  const files = fs.readdirSync(src);
  for (const file of files) {
    const srcPath = path.join(src, file);
    const destPath = path.join(dest, file);
    const stat = fs.statSync(srcPath);
    if (stat.isDirectory()) {
      fs.mkdirSync(destPath, { recursive: true });
      copyRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

copyRecursive(templateDir, root);

// install deps
console.log("📦 Installing dependencies...");
execSync("yarn", { cwd: root, stdio: "inherit" });

console.log("✅ Done!");
console.log(`👉 cd ${projectName} && yarn dev`);
