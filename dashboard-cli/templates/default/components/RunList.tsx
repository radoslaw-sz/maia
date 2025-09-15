'use client';

import { useEffect, useState, useMemo } from 'react';
import type { TestReport } from '@/types';

// Internal data structure for the view, adapted from the wireframe
interface Test {
  id: string;
  name: string;
  status: 'passed' | 'failed' | 'running';
  timestamp: string;
  duration: string;
}

interface Run {
  id: string;
  name: string;
  timestamp: string;
  stats: {
    passed: number;
    failed: number;
    running: number;
    total: number;
  };
  duration: string;
  tests: Test[];
}


const RunList = ({ onSelectRun }: { onSelectRun: (runId: string) => void }) => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null); // Track selected run
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');

  useEffect(() => {
    const fetchAndProcessRuns = async () => {
      setLoading(true);
      try {
        const runIdsRes = await fetch('/api/runs');
        if (!runIdsRes.ok) throw new Error('Failed to fetch run IDs. Please check if you have set TEST_REPORTS_DIR. See more here: https://www.maiaframework.com/docs/dashboard');
        const runIds: string[] = await runIdsRes.json();

        const runsData = await Promise.all(
          runIds.map(async (id) => {
            try {
              const reportsRes = await fetch(`/api/runs/${id}`);
              if (!reportsRes.ok) return { id, reports: [] };
              const reports: TestReport[] = await reportsRes.json();
              return { id, reports };
            } catch (e) {
              console.error(`Failed to fetch details for run ${id}:`, e);
              return { id, reports: [] };
            }
          })
        );

        const transformedRuns: Run[] = runsData.map(({ id, reports }) => {
          const tests: Test[] = reports.map(report => {
            return {
              id: report.test_id,
              name: report.test_name,
              status: report.status as 'passed' | 'failed' | 'running',
              timestamp: report.start_time,
              duration: `${((new Date(report.end_time).getTime() - new Date(report.start_time).getTime()) / 1000).toFixed(1)}s`,
            };
          });

          const stats = {
            passed: tests.filter(t => t.status === 'passed').length,
            failed: tests.filter(t => t.status === 'failed').length,
            running: tests.filter(t => t.status === 'running').length,
            total: tests.length,
          };

          const runStartTime = reports.reduce((min, r) => Math.min(min, new Date(r.start_time).getTime()), new Date(reports[0]?.start_time).getTime());
          const runEndTime = reports.reduce((max, r) => Math.max(max, new Date(r.end_time).getTime()), new Date(reports[0]?.end_time).getTime());
          const durationMs = runEndTime - runStartTime;
          
          const formatDuration = (seconds: number) => {
            if (seconds < 0 || !seconds) return 'N/A';
            if (seconds < 60) return `${seconds.toFixed(1)}s`;
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = (seconds % 60).toFixed(1);
            return `${minutes}m ${remainingSeconds}s`;
          };

          return {
            id: id,
            name: id.replace(/_/g, ' ').replace(/(^\w{1})|(\s+\w{1})/g, letter => letter.toUpperCase()),
            timestamp: reports.length > 0 ? new Date(runStartTime).toISOString() : new Date().toISOString(),
            stats: stats,
            duration: formatDuration(durationMs / 1000),
            tests: tests,
          };
        });

        const sortedRuns = transformedRuns.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        setRuns(sortedRuns);

      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAndProcessRuns();
  }, []);

  const handleSelectRun = (runId: string) => {
    setSelectedRunId(runId);
    onSelectRun(runId);
  };

  const getRunDateGroup = (timestamp: string): string => {
    const runDate = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);

    if (runDate.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (runDate.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return runDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
  };

  const filteredRuns = useMemo(() => {
    return runs
      .filter(run => 
        run.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        run.tests.some(test => test.name.toLowerCase().includes(searchTerm.toLowerCase()))
      )
      .filter(run => {
        if (activeFilter === 'all') return true;
        return run.tests.some(test => test.status === activeFilter);
      });
  }, [runs, searchTerm, activeFilter]);

  const groupedRuns = useMemo(() => {
    const groups: { [key: string]: Run[] } = {};
    filteredRuns.forEach(run => {
      const dateGroup = getRunDateGroup(run.timestamp);
      if (!groups[dateGroup]) {
        groups[dateGroup] = [];
      }
      groups[dateGroup].push(run);
    });
    return groups;
  }, [filteredRuns]);

  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const allGroupNames = Object.keys(groupedRuns);
    if (allGroupNames.length > 0) {
      const initialState = { ...collapsedGroups };
      const groupToExpand = allGroupNames.includes('Today') ? 'Today' : allGroupNames[0];

      allGroupNames.forEach(group => {
        if (initialState[group] === undefined) {
          initialState[group] = group !== groupToExpand;
        }
      });
      setCollapsedGroups(initialState);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupedRuns]);

  const toggleGroup = (groupName: string) => {
    setCollapsedGroups(prev => ({ ...prev, [groupName]: !prev[groupName] }));
  };

  const getStatusStyles = (status: Test['status']) => {
    switch (status) {
      case 'passed': return 'bg-[rgba(34,197,94,0.2)] border-[rgba(34,197,94,0.3)] text-[#22c55e]';
      case 'failed': return 'bg-[rgba(239,68,68,0.2)] border-[rgba(239,68,68,0.3)] text-[#ef4444]';
      case 'running': return 'bg-[rgba(245,158,11,0.2)] border-[rgba(245,158,11,0.3)] text-[#f59e0b] animate-pulse';
    }
  };

  if (loading) return <div className="p-6 text-[#9ca3af]">Loading runs...</div>;
  if (error) return <div className="p-6 text-red-500">Error: {error}</div>;

  const sortedGroupKeys = Object.keys(groupedRuns).sort((a, b) => {
    if (a === 'Today') return -1;
    if (b === 'Today') return 1;
    if (a === 'Yesterday') return -1;
    if (b === 'Yesterday') return 1;
    return new Date(b).getTime() - new Date(a).getTime();
  });

  return (
    <div className="w-[380px] bg-[rgba(26,26,46,0.95)] border-r border-l border-t border-[#2a2d47] backdrop-blur-sm flex flex-col h-full">
      <div className="p-6 border-b border-[#2a2d47] bg-gradient-to-br from-[#1a1a2e] to-[#16213e]">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-[#64b5f6] to-[#1e88e5] text-transparent bg-clip-text mb-1">Runs</h2>
        <p className="text-sm text-[#9ca3af]">Browse test execution history</p>
      </div>

      <div className="p-6 border-b border-[rgba(42,45,71,0.6)]">
        <div className="relative">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#9ca3af]">🔍</span>
          <input
            type="text"
            placeholder="Search runs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[rgba(15,15,35,0.8)] border border-[#2a2d47] rounded-xl py-3 pl-11 pr-4 text-[#e0e6ed] focus:outline-none focus:border-[#64b5f6] transition"
          />
        </div>
        <div className="flex gap-2 mt-3">
          {(['all', 'passed', 'failed', 'running'] as const).map(filter => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${activeFilter === filter ? 'bg-[rgba(100,181,246,0.2)] border-[#64b5f6] text-[#64b5f6]' : 'bg-[rgba(15,15,35,0.6)] border-[#2a2d47] text-[#9ca3af] hover:bg-[rgba(100,181,246,0.1)] hover:border-[#64b5f680]'}`}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 custom-scrollbar">
        <div className="p-6 space-y-4">
          {sortedGroupKeys.map((dateGroup) => (
            <div key={dateGroup}>
              <div 
                className={`date-separator text-xs font-semibold text-[#64b5f6] uppercase tracking-wider mb-2 sticky top-0 bg-[rgba(26,26,46,0.95)] z-10 py-2 border-b border-[rgba(42,45,71,0.6)] flex justify-between items-center cursor-pointer ${!collapsedGroups[dateGroup] ? 'expanded' : ''}`}
                onClick={() => toggleGroup(dateGroup)}
              >
                <span>{dateGroup}</span>
                <svg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' strokeWidth={2} stroke='currentColor' className='w-4 h-4 expand-icon transition-transform'>
                  <path strokeLinecap='round' strokeLinejoin='round' d='M8.25 4.5l7.5 7.5-7.5 7.5' />
                </svg>
              </div>
              <div className={`${collapsedGroups[dateGroup] ? 'hidden' : ''}`}>
                <div className="space-y-2 pt-2">
                {groupedRuns[dateGroup].map(run => (
                  <div 
                    key={run.id} 
                    className={`run-item cursor-pointer p-5 rounded-xl transition-all ${selectedRunId === run.id ? 'border-[#64b5f6] bg-[rgba(100,181,246,0.1)] translate-x-1' : 'border-[rgba(42,45,71,0.6)] bg-[rgba(15,15,35,0.4)] hover:border-[rgba(100,181,246,0.5)] hover:bg-[rgba(15,15,35,0.6)] hover:translate-x-1'}`}
                    onClick={() => handleSelectRun(run.id)}
                  >
                    <div className="run-header flex items-start justify-between mb-3">
                      <div className="run-info flex-1">
                        <h3 className="run-name text-lg font-semibold text-[#e0e6ed] mb-1">{run.name}</h3>
                        <p className="run-meta text-xs text-[#9ca3af] flex gap-3">{new Date(run.timestamp).toLocaleTimeString()}</p>
                      </div>
                      <span className="run-duration text-sm font-medium text-[#64b5f6]">{run.duration}</span>
                    </div>
                    <div className="run-stats flex items-center gap-2 mb-3">
                      <div className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${getStatusStyles('passed')}`}>{run.stats.passed} passed</div>
                      {run.stats.failed > 0 && <div className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${getStatusStyles('failed')}`}>{run.stats.failed} failed</div>}
                      {run.stats.running > 0 && <div className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${getStatusStyles('running')}`}>{run.stats.running} running</div>}
                      <div className="text-sm text-[#9ca3af]">/ {run.stats.total} total</div>
                    </div>
                    <div className="run-progress w-full h-1 bg-[rgba(42,45,71,0.6)] rounded-full overflow-hidden">
                      <div 
                        className={`progress-bar h-full rounded-full ${run.stats.failed > 0 ? 'bg-gradient-to-r from-[#ef4444] to-[#dc2626]' : run.stats.running > 0 ? 'bg-gradient-to-r from-[#f59e0b] to-[#d97706] animate-pulse' : 'bg-gradient-to-r from-[#22c55e] to-[#16a34a]'}`}
                        style={{ width: `${(run.stats.passed / run.stats.total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
        </div>
      </div>
    </div>
  )
}

export default RunList;