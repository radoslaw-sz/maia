'use client';

import { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import type { TestReport } from '@/types';

const ReportView = ({ runId }: { runId: string }) => {
  const [reports, setReports] = useState<TestReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;

    const fetchReports = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/runs/${runId}`);
        if (!res.ok) {
          throw new Error('Failed to fetch reports');
        }
        const data: TestReport[] = await res.json();
        setReports(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [runId]);

  const runOverviewStats = useMemo(() => {
    const total = reports.length;
    const passed = reports.filter(r => r.status === 'passed').length;
    const failed = reports.filter(r => r.status === 'failed').length;
    const running = reports.filter(r => r.status === 'running').length;

    let totalDuration = 0;
    let runStartTimeVal = 'N/A';

    if (reports.length > 0) {
      const startTime = reports.reduce((min, r) => Math.min(min, new Date(r.start_time).getTime()), new Date(reports[0]?.start_time).getTime());
      const endTime = reports.reduce((max, r) => Math.max(max, new Date(r.end_time).getTime()), new Date(reports[0]?.end_time).getTime());
      totalDuration = (endTime - startTime) / 1000; // in seconds
      runStartTimeVal = new Date(startTime).toLocaleString();
    }

    const formatDuration = (seconds: number) => {
      if (seconds < 0 || !seconds) return 'N/A';
      if (seconds < 60) return `${seconds.toFixed(1)}s`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = (seconds % 60).toFixed(1);
      return `${minutes}m ${remainingSeconds}s`;
    };

    const runSource = 'Manual run';

    return {
      total, passed, failed, running,
      totalDuration: formatDuration(totalDuration),
      runStartTime: runStartTimeVal,
      runSource,
    };
  }, [reports]);

  if (loading) return <div>Loading reports...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="flex-1 bg-[#0f0f23] overflow-hidden flex flex-col">
      <div className="p-8 pb-6 border-b border-[rgba(42,45,71,0.6)] bg-gradient-to-br from-[rgba(26,26,46,0.3)] to-[rgba(22,33,62,0.3)]">
        <h1 className="text-3xl font-bold mb-2 bg-gradient-to-br from-[#64b5f6] to-[#42a5f5] text-transparent bg-clip-text">Test Run: {runId}</h1>
        <p className="text-base text-[#9ca3af] mb-4">{runOverviewStats.runSource} • {runOverviewStats.runStartTime} • Duration: {runOverviewStats.totalDuration}</p>
        
        <div className="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-4">
          <div className="bg-[rgba(15,15,35,0.6)] border border-[rgba(42,45,71,0.6)] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold mb-1 text-[#22c55e]">{runOverviewStats.passed}</div>
            <div className="text-sm text-[#9ca3af]">Tests Passed</div>
          </div>
          <div className="bg-[rgba(15,15,35,0.6)] border border-[rgba(42,45,71,0.6)] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold mb-1 text-[#ef4444]">{runOverviewStats.failed}</div>
            <div className="text-sm text-[#9ca3af]">Tests Failed</div>
          </div>
          <div className="bg-[rgba(15,15,35,0.6)] border border-[rgba(42,45,71,0.6)] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold mb-1 text-[#f59e0b]">{runOverviewStats.running}</div>
            <div className="text-sm text-[#9ca3af]">Tests Running</div>
          </div>
          <div className="bg-[rgba(15,15,35,0.6)] border border-[rgba(42,45,71,0.6)] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold mb-1 text-[#64b5f6]">{runOverviewStats.totalDuration}</div>
            <div className="text-sm text-[#9ca3af]">Total Duration</div>
          </div>
        </div>
      </div>

      <div className="flex-1 p-6 px-8 overflow-y-auto">
        <div className="grid grid-cols-[repeat(auto-fill,minmax(380px,1fr))] gap-5">
          {reports.map(report => (
            <Link key={report.test_id} href={`/run/${runId}/tests/${report.test_id}`}>
              <div className={`bg-[rgba(26,26,46,0.6)] border border-[rgba(42,45,71,0.6)] rounded-2xl p-6 cursor-pointer transition-all duration-300 backdrop-blur-sm hover:border-[rgba(100,181,246,0.6)] hover:bg-[rgba(26,26,46,0.8)] hover:-translate-y-1 shadow-lg ${report.status === 'passed' ? 'border-[rgba(34,197,94,0.3)]' : report.status === 'failed' ? 'border-[rgba(239,68,68,0.3)]' : 'border-[rgba(245,158,11,0.3)]'}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="text-lg font-semibold mb-2 text-[#e0e6ed] flex-1 min-w-0 break-words">{report.test_name}</div>
                  <div className={`px-3 py-1.5 rounded-xl text-xs font-semibold uppercase tracking-wide flex-shrink-0 ${report.status === 'passed' ? 'bg-[rgba(34,197,94,0.2)] border border-[rgba(34,197,94,0.3)] text-[#22c55e]' : report.status === 'failed' ? 'bg-[rgba(239,68,68,0.2)] border border-[rgba(239,68,68,0.3)] text-[#ef4444]' : 'bg-[rgba(245,158,11,0.2)] border border-[rgba(245,158,11,0.3)] text-[#f59e0b] animate-pulse'}`}>{report.status}</div>
                </div>
                <div className="flex justify-between items-center text-sm text-[#9ca3af] mb-4">
                  <span className="text-[#9ca3af]">{new Date(report.start_time).toLocaleTimeString()}</span>
                  <span className="text-[#64b5f6] font-medium">{((new Date(report.end_time).getTime() - new Date(report.start_time).getTime()) / 1000).toFixed(1)}s</span>
                </div>
                <div className="mb-4">
                  <div className="text-xs text-[#9ca3af] mb-2">Agents involved:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {report.participants.filter(p => p.type === 'agent').map(agent => (
                      <span key={agent.id} className="bg-[rgba(100,181,246,0.15)] border border-[rgba(100,181,246,0.3)] text-[#64b5f6] px-2.5 py-1 rounded-xl text-xs font-medium">{agent.name}</span>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 pt-4 border-t border-[rgba(42,45,71,0.6)]">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-[#e0e6ed] mb-1">{report.sessions.reduce((acc, session) => acc + session.messages.length, 0)}</div>
                    <div className="text-xs text-[#9ca3af]">Messages</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-[#e0e6ed] mb-1">{report.sessions.reduce((acc, session) => acc + session.messages.filter(msg => msg.sender_type === 'tool').length, 0)}</div>
                    <div className="text-xs text-[#9ca3af]">Tools</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-[#e0e6ed] mb-1">{(() => {
                      if (!report.assertions || report.assertions.length === 0) {
                        return '100%';
                      }
                      const passedAssertions = report.assertions.filter(assertion => assertion.status === 'passed').length;
                      const successRate = (passedAssertions / report.assertions.length) * 100;
                      return `${successRate.toFixed(0)}%`;
                    })()}</div>
                    <div className="text-xs text-[#9ca3af]">Success Rate</div>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ReportView;
