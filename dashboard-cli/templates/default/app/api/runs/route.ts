import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  const reportsDir = process.env.TEST_REPORTS_DIR || 'test_reports';
  const dir = path.resolve(process.cwd(), '..', reportsDir);

  try {
    const runDirs = fs.readdirSync(dir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);
    return NextResponse.json(runDirs);
  } catch (error) {
    console.error("Error reading test runs:", error);
    return NextResponse.json({ error: 'Failed to read test runs' }, { status: 500 });
  }
}
