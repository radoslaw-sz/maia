import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: Request, { params }: { params: { runId: string } }) {
  const { runId } = await params;
  const reportsDir = process.env.TEST_REPORTS_DIR || 'test_reports';
  const runPath = path.resolve(process.cwd(), '..', reportsDir, runId);

  try {
    const files = fs.readdirSync(runPath);
    const reports = files
      .filter(file => file.endsWith('.json') && file !== 'test_results.json' && file !== 'pytest_raw_report.json')
      .map(file => {
        const content = fs.readFileSync(path.join(runPath, file), 'utf-8');
        const report = JSON.parse(content);
        report.test_id = file.replace('.json', '');
        return report;
      });
    return NextResponse.json(reports);
  } catch (error) {
    console.error(`Error reading reports for run ${runId}:`, error);
    return NextResponse.json({ error: `Failed to read reports for run ${runId}` }, { status: 500 });
  }
}
