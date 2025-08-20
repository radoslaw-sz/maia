import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: Request,
  { params }: { params: { runId: string; testId: string } }
) {
  const { runId, testId } = await params;
  const reportsDir = process.env.TEST_REPORTS_DIR || 'test_reports';
  const filePath = path.resolve(process.cwd(), '..', reportsDir, runId, `${testId}.json`);

  try {
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: 'Test report not found' }, { status: 404 });
    }
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const report = JSON.parse(fileContent);
    return NextResponse.json(report);
  } catch (error) {
    console.error(`Error reading test report ${runId}/${testId}:`, error);
    return NextResponse.json({ error: 'Failed to read test report' }, { status: 500 });
  }
}
