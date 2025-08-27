'use client';

import { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import type { TestReport } from '@/types';

const TestView = ({ runId, testId }: { runId: string, testId: string }) => {
  const [report, setReport] = useState<TestReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [activeTab, setActiveTab] = useState('timeline'); // New state for active tab

  const toolNames = useMemo(() => {
    if (!report) return new Set<string>();
    return new Set(report.participants.filter(p => p.type === 'tool').map(t => t.name));
  }, [report]);

  const agentNames = useMemo(() => {
    if (!report) return new Set<string>();
    return new Set(report.participants.filter(p => p.type === 'agent').map(a => a.name));
  }, [report]);

  useEffect(() => {
    if (!runId || !testId) return;

    const fetchReport = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/runs/${runId}/tests/${testId}`);
        if (!res.ok) {
          throw new Error('Failed to fetch test report');
        }
        const data = await res.json();
        setReport(data);
        if (data.sessions && data.sessions.length > 0) {
          setSelectedSessionId(data.sessions[0].id);
        }
      } catch (err) {
        const error = err as unknown as any
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [runId, testId]);

  if (loading) return <div className="text-[#e0e6ed]">Loading test report...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;
  if (!report) return <div className="text-[#9ca3af]">No report found.</div>;

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  const calculateDuration = (start: string, end: string) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    const durationMs = endDate.getTime() - startDate.getTime();
    return (durationMs / 1000).toFixed(2) + 's';
  };

  const formatJson = (content: string) => {
    try {
      return JSON.stringify(JSON.parse(content), null, 2);
    } catch (e) {
      return content;
    }
  };

  const getDotColorClass = (msg: any) => {
    if (toolNames.has(msg.sender)) {
      return 'bg-[#f59e0b] border-[#0f0f23]';
    }
    if (msg.metadata?.tool_args) {
      return 'bg-[#f59e0b] border-[#0f0f23]';
    }
    if (msg.metadata?.type === 'error') {
      return 'bg-[#f44336] border-[#0f0f23]';
    }
    return 'bg-[#64b5f6] border-[#0f0f23]';
  };

  const countMessages = (testReport: TestReport) => {
    let count = 0;
    testReport.sessions.forEach(session => count += session.messages.length)
    return count
  }

  const countAgentMessages = (testReport: TestReport, agentName: string) => {
    let count = 0;
    testReport.sessions.forEach(session => {
      session.messages.forEach(message => {
        if (message.sender === agentName) {
          count++;
        }
      });
    });
    return count
  }

  const countToolCalls = (testReport: TestReport) => {
    let count = 0;
    testReport.sessions.forEach(session => {
      session.messages.forEach(message => {
        if (message.receiver_type === "tool") {
          count++;
        }
      });
    });
    return count;
  }

  const countSingleToolCalls = (testReport: TestReport, toolName: string) => {
    let count = 0;
    testReport.sessions.forEach(session => {
      session.messages.forEach(message => {
        if (message.receiver_type === "tool" && message.receiver === toolName) {
          count++;
        }
      });
    });
    return count;
  }

  const countUniqueToolsUsedByAgent = (testReport: TestReport, agentName: string) => {
    const usedTools = new Set<string>();
    testReport.sessions.forEach(session => {
        session.messages.forEach(msg => {
            if (msg.sender === agentName && msg.receiver_type === 'tool' && msg.receiver) {
                usedTools.add(msg.receiver);
            }
        });
    });
    return usedTools.size;
  }

  const calculateSuccessRate = (testReport: TestReport) => {
    if (!testReport.assertions || testReport.assertions.length === 0) {
      return '100%';
    }
    const passedAssertions = testReport.assertions.filter(assertion => assertion.status === 'passed').length;
    const successRate = (passedAssertions / testReport.assertions.length) * 100;
    return `${successRate.toFixed(0)}%`;
  };

  const calculateAvgResponseTime = (testReport: TestReport) => {
    const agentNames = new Set(testReport.participants.filter(p => p.type === 'agent').map(a => a.name));
    const responseTimes: number[] = [];

    testReport.sessions.forEach(session => {
        for (let i = 0; i < session.messages.length - 1; i++) {
            const currentMsg = session.messages[i];
            const nextMsg = session.messages[i+1];

            if (!agentNames.has(currentMsg.sender) && agentNames.has(nextMsg.sender)) {
                const requestTimestamp = new Date(currentMsg.timestamp).getTime();
                const responseTimestamp = new Date(nextMsg.timestamp).getTime();
                const diff = responseTimestamp - requestTimestamp;
                if (diff >= 0) {
                    responseTimes.push(diff);
                }
            }
        }
    });

    if (responseTimes.length === 0) {
        return 'N/A';
    }

    const avgTimeMs = responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length;
    
    const avgTimeS = avgTimeMs / 1000;
    if (avgTimeS < 1) {
        return `${avgTimeMs.toFixed(0)}ms`;
    }
    if (avgTimeS < 60) {
        return `${avgTimeS.toFixed(2)}s`;
    }
    const minutes = Math.floor(avgTimeS / 60);
    const remainingSeconds = (avgTimeS % 60).toFixed(2);
    return `${minutes}m ${remainingSeconds}s`;
  }

  const getUniqueTools = (testReport: TestReport) => {
    return testReport.participants.filter(p => p.type === 'tool').map(t => t.name);
  };

  const selectedSession = report.sessions.find(s => s.id === selectedSessionId);

  return (
    <div className="max-w-screen-2xl mx-auto p-5 bg-[rgba(26,26,46,0.95)] border-l border-t border-[#2a2d47]">
      <Link href={`/?runId=${runId}`} className="inline-flex items-center text-[#64b5f6] hover:text-[#42a5f5] transition-colors mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 mr-2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        Back to Run Overview
      </Link>
      {/* Header */}
      <div className="gradient-bg border border-[#2a2d47] rounded-2xl p-8 mb-6 backdrop-blur-sm">
        <div className="flex items-center gap-4 mb-2">
          <h1 className="text-4xl font-bold gradient-text">{report.test_name}</h1>
          <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full font-semibold text-xs uppercase ${report.status === 'passed' ? 'bg-[rgba(34,197,94,0.1)] border-[rgba(34,197,94,0.3)] text-[#22c55e]' : 'bg-[rgba(255,0,0,0.1)] border-[rgba(255,0,0,0.3)] text-[#ff0000]'}`}>
            <div className={`w-2 h-2 rounded-full ${report.status === 'passed' ? 'bg-[#22c55e]' : 'bg-[#ff0000]'}`}></div>
            {report.status}
          </div>
        </div>
        <div className="flex gap-8 mb-5 text-sm text-[#9ca3af]">
          <span>Test ID: {testId}</span>
          <span>Duration: {calculateDuration(report.start_time, report.end_time)}</span>
          <span>Started: {formatTime(report.start_time)}</span>
          <span>Ended: {formatTime(report.end_time)}</span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mt-5">
          <div className="bg-[rgba(26,26,46,0.6)] border border-[#2a2d47] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold gradient-text mb-1">{countMessages(report)}</div>
            <div className="text-xs text-[#9ca3af] uppercase tracking-wider">Total Messages</div>
          </div>
          <div className="bg-[rgba(26,26,46,0.6)] border border-[#2a2d47] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold gradient-text mb-1">{countToolCalls(report)}</div>
            <div className="text-xs text-[#9ca3af] uppercase tracking-wider">Tool Calls</div>
          </div>
          <div className="bg-[rgba(26,26,46,0.6)] border border-[#2a2d47] rounded-xl p-4 text-center metric-card clickable" onClick={() => setActiveTab('assertions')}>
            <div className="text-3xl font-bold gradient-text mb-1">{calculateSuccessRate(report)}</div>
            <div className="text-xs text-[#9ca3af] uppercase tracking-wider">Success Rate</div>
          </div>
          <div className="bg-[rgba(26,26,46,0.6)] border border-[#2a2d47] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold gradient-text mb-1">{calculateAvgResponseTime(report)}</div>
            <div className="text-xs text-[#9ca3af] uppercase tracking-wider">Avg Response</div>
          </div>
          {/* <div className="bg-[rgba(26,26,46,0.6)] border border-[#2a2d47] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold gradient-text mb-1">N/A</div>
            <div className="text-xs text-[#9ca3af] uppercase tracking-wider">Agent Handoffs</div>
          </div> */}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-6 mb-6">
        {/* Sidebar */}
        <div className="gradient-bg border border-[#2a2d47] rounded-2xl p-6 h-fit backdrop-blur-sm">
          {/* Agents Section */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4 text-[#e0e6ed]">Participating Agents</h3>
            <div className="flex flex-col gap-3">
              {report.participants.filter(p => p.type === 'agent').map((agent, index) => {
                const AGENT_AVATAR_GRADIENTS = [
                  "agent-avatar-customer",
                  "agent-avatar-inventory",
                  "agent-avatar-pricing",
                  "agent-avatar-analytics",
                ];
                const gradientClass = AGENT_AVATAR_GRADIENTS[index % AGENT_AVATAR_GRADIENTS.length];
                return (
                <div key={agent.id} className="flex items-center gap-3 p-3 bg-[rgba(100,181,246,0.1)] border border-[#2a2d47] rounded-xl hover:border-accent-blue hover:-translate-y-px transition-all duration-200 agent-item">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm text-white ${gradientClass}`}>{agent.name.substring(0, 2).toUpperCase()}</div>
                  <div className="flex-grow">
                    <div className="font-semibold agent-name text-[#e0e6ed]">{agent.name}</div>
                    <div className="text-xs text-[#9ca3af]">{agent.metadata.model}</div>
                    <div className="flex gap-3 text-xs gradient-text">
                      <span>{`${countAgentMessages(report, agent.name)} ${countAgentMessages(report, agent.name) === 1 ? 'msg' : 'msgs'}`}</span>
                      <span>{`${countUniqueToolsUsedByAgent(report, agent.name)} ${countUniqueToolsUsedByAgent(report, agent.name) === 1 ? 'tool' : 'tools'}`}</span>
                    </div>
                  </div>
                </div>
              )})}
            </div>
          </div>

          {/* Tools Section */}
          {getUniqueTools(report).length > 0 && <div>
            <h3 className="text-lg font-semibold mb-4 text-[#e0e6ed]">Tools Used</h3>
            <div className="flex flex-col gap-2">
              {getUniqueTools(report).map(tool => (
                <div key={tool} className="flex items-center justify-between p-2 px-3 bg-dark-bg/40 border border-[#2a2d47] rounded-lg text-sm hover:bg-[rgba(15,15,35,0.6)] transition-colors tool-item">
                  <span className="text-[#e0e6ed] tool-name">{tool}</span>
                  <span className="bg-[rgba(100,181,246,0.2)] text-[#64b5f6] px-2 py-1 rounded-xl text-xs font-semibold">{countSingleToolCalls(report, tool)}</span>
                </div>
              ))}
            </div>
          </div>}
        </div>

        {/* Content Area */}
        <div className="gradient-bg border border-[#2a2d47] rounded-2xl backdrop-blur-sm overflow-hidden">
          <div className="tab-bar flex border-b border-[#2a2d47]">
            <button
              className={`tab flex-1 p-4 text-center cursor-pointer transition-all font-semibold flex items-center gap-2 justify-center ${activeTab === 'timeline' ? 'active bg-[rgba(26,26,46,0.8)] text-[#64b5f6] border-b-2 border-[#64b5f6]' : 'bg-[rgba(15,15,35,0.4)] text-[#9ca3af] hover:bg-[rgba(26,26,46,0.6)] hover:text-[#e0e6ed]'}`}
              onClick={() => setActiveTab('timeline')}
            >
              <div className="tab-icon w-4 h-4 rounded-full bg-[#64b5f6]"></div>
              Timeline
            </button>
            <button
              className={`tab flex-1 p-4 text-center cursor-pointer transition-all font-semibold flex items-center gap-2 justify-center ${activeTab === 'assertions' ? 'active bg-[rgba(26,26,46,0.8)] text-[#64b5f6] border-b-2 border-[#64b5f6]' : 'bg-[rgba(15,15,35,0.4)] text-[#9ca3af] hover:bg-[rgba(26,26,46,0.6)] hover:text-[#e0e6ed]'}`}
              onClick={() => setActiveTab('assertions')}
            >
              <div className={`tab-icon w-4 h-4 rounded-full ${report.assertions.filter(a => a.status === 'failed').length > 0 ? 'bg-[#ef4444]' : 'bg-[#22c55e]'}`}></div>
              Assertions
              {report.assertions.filter(a => a.status === 'failed').length > 0 && (
                <div className="badge warning flex items-center gap-1 px-2 py-1 rounded-xl text-xs font-semibold bg-[rgba(239,68,68,0.1)] border border-[rgba(239,68,68,0.3)] text-[#ef4444]">
                  <div className="badge-icon w-1.5 h-1.5 rounded-full bg-[#ef4444]"></div>
                  {report.assertions.filter(a => a.status === 'failed').length} Failed
                </div>
              )}
            </button>
          </div>

          <div className="tab-content p-6">
            {activeTab === 'timeline' && (
              <div id="timeline">
                {/* Session Selector (always rendered) */}
                <div className="flex items-center gap-2 mb-4">
                  <label htmlFor="session-select" className="text-sm font-medium text-[#9ca3af]">Session:</label>
                  <select
                    id="session-select"
                    value={selectedSessionId || ''}
                    onChange={(e) => setSelectedSessionId(e.target.value)}
                    className="bg-[rgba(15,15,35,0.8)] border border-[#2a2d47] rounded-lg text-sm text-white py-2 pl-3 pr-8 appearance-none focus:outline-none focus:border-accent-blue transition-colors"
                    style={{ 
                      backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2364b5f6' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                      backgroundPosition: 'right 0.5rem center',
                      backgroundRepeat: 'no-repeat',
                      backgroundSize: '1.5em 1.5em',
                    }}
                  >
                    {report.sessions.map((session) => (
                      <option key={session.id} value={session.id}>
                        {session.id}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-semibold text-[#e0e6ed]">Interaction Timeline</h2>
                  {/* Filters */}
                  <div className="flex gap-3">
                    {['all', 'messages', 'tools'].map(filter => (
                      <button
                        key={filter}
                        onClick={() => setActiveFilter(filter)}
                        className={`px-4 py-2 rounded-lg text-sm font-semibold cursor-pointer transition-all ${activeFilter === filter ? 'bg-[rgba(100,181,246,0.2)] border border-[#64b5f6] text-[#64b5f6]' : 'bg-[rgba(15,15,35,0.6)] border border-[#2a2d47] text-[#e0e6ed] hover:bg-[rgba(100,181,246,0.2)] hover:border-[#64b5f6] hover:text-[#64b5f6]'}`}
                      >
                        {filter.charAt(0).toUpperCase() + filter.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="relative">
                  {/* Main vertical line */}
                  <div className="absolute left-[19px] top-0 w-0.5 bg-gradient-to-b from-[#64b5f6] via-[#42a5f5] to-[#1e88e5] h-full"></div>

                  {selectedSession ? (
                    selectedSession.messages.filter(msg => {
                      if (activeFilter === 'all') return true;
                      if (activeFilter === 'messages') {
                        return agentNames.has(msg.sender) || msg.sender === 'user';
                      }
                      if (activeFilter === 'tools') {
                        return toolNames.has(msg.sender) || msg.receiver_type === 'tool';
                      }
                      return true;
                    }).map((msg, index) => (
                      <div key={msg.message_id} className="flex items-start mb-6">
                        {/* Left column: Dot */}
                        <div className="relative w-10 flex-shrink-0">
                          {/* Dot */}
                          <div className={`absolute left-[12px] top-[8px] w-4 h-4 rounded-full border-2 z-50 ${getDotColorClass(msg)}`}></div>
                        </div>
                        
                        {/* Right column: Card content */}
                        <div className="flex-grow ml-4 bg-[rgba(15,15,35,0.6)] border border-[#2a2d47] rounded-xl p-5 hover:border-[rgba(100,181,246,0.5)] hover:-translate-y-px transition-all duration-200">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2 font-semibold text-[#e0e6ed]">
                              <div className={`w-2 h-2 ${getDotColorClass(msg)} rounded-full`}></div>
                              {/* Determine type of message for display */}
                              {toolNames.has(msg.sender) ? `Tool response` : msg.metadata?.tool_args ? `🔧 ${msg.metadata.receiver}` : msg.sender === 'user' ? 'User Message' : 'Agent Message'}
                            </div>
                            <div className="text-xs text-[#9ca3af]">{new Date(msg.timestamp).toLocaleTimeString()}</div>
                          </div>
                          <div className="flex items-center gap-2 mb-4">
                            <span className="bg-[rgba(100,181,246,0.1)] border border-[rgba(100,181,246,0.3)] text-[#64b5f6] px-2.5 py-1 rounded-2xl text-xs font-medium">{msg.sender}</span>
                            {/* Add receiver if available in metadata */}
                            {msg.receiver && (
                              <>
                                <span className="text-[#9ca3af]">→</span>
                                <span className="bg-[rgba(100,181,246,0.1)] border border-[rgba(100,181,246,0.3)] text-[#64b5f6] px-2.5 py-1 rounded-2xl text-xs font-medium">{msg.receiver}</span>
                              </>
                            )}
                          </div>
                          {toolNames.has(msg.sender) ? (
                            <div className="bg-orange-300/10 border border-orange-600/30 rounded-lg p-4">
                              <pre className="font-mono text-sm text-orange-400 whitespace-pre-wrap">{formatJson(msg.content)}</pre>
                            </div>
                          ) : msg.metadata?.tool_args ? (
                            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 mt-3">
                              <pre className="font-mono text-xs text-yellow-200">{JSON.stringify(msg.metadata.tool_args, null, 2)}</pre>
                            </div>
                          ) : (
                            <div className="bg-black/20 border border-[#2a2d47] rounded-lg p-4 mb-4 font-mono text-sm leading-relaxed text-gray-300">
                              <pre className="whitespace-pre-wrap ">{msg.content}</pre>
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center text-[#9ca3af] py-10">Select a session to view its timeline.</div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'assertions' && (
              <div id="assertions">
                <div className="assertions-header flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-semibold text-[#e0e6ed]">Test Assertions</h2>
                  <div className="assertions-summary flex items-center gap-4">
                    <div className="summary-metric passed-metric flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-[rgba(34,197,94,0.1)] border border-[rgba(34,197,94,0.3)] text-[#22c55e]">
                      <div className="status-icon w-2 h-2 rounded-full bg-[#22c55e]"></div>
                      {report.assertions.filter(a => a.status === 'passed').length} Passed
                    </div>
                    <div className="summary-metric failed-metric flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-[rgba(239,68,68,0.1)] border border-[rgba(239,68,68,0.3)] text-[#ef4444]">
                      <div className="status-icon w-2 h-2 rounded-full bg-[#ef4444]"></div>
                      {report.assertions.filter(a => a.status === 'failed').length} Failed
                    </div>
                  </div>
                </div>
                
                {report.assertions.length > 0 ? (
                  report.assertions.map(assertion => {
                    return (
                      <div key={assertion.id} className={`assertion-item bg-[rgba(15,15,35,0.6)] border border-[#2a2d47] rounded-xl p-5 mb-3 transition-all ${assertion.status === 'passed' ? 'border-l-4 border-[#22c55e]' : 'border-l-4 border-[#ef4444]'}`}>
                        <div className="assertion-header flex items-start justify-between">
                          <div className="flex-grow pr-4">
                            <div className="assertion-name text-base font-semibold text-[#e0e6ed]">{assertion.assertion_name}</div>
                            {assertion.description && (
                              <div className="assertion-description text-sm text-[#9ca3af] mt-1">
                                {assertion.description}
                              </div>
                            )}
                            {assertion.metadata?.message?.content && (
                              <div className="assertion-description text-sm text-[#9ca3af] mt-1">
                                {assertion.metadata.message.content}
                              </div>
                            )}
                          </div>
                          <div className={`assertion-status flex-shrink-0 flex items-center gap-2 px-3 py-1 rounded-2xl text-xs font-semibold uppercase ${assertion.status === 'passed' ? 'bg-[rgba(34,197,94,0.1)] text-[#22c55e]' : 'bg-[rgba(239,68,68,0.1)] text-[#ef4444]'}`}>
                            <div className={`status-icon w-2 h-2 rounded-full ${assertion.status === 'passed' ? 'bg-[#22c55e]' : 'bg-[#ef4444]'}`}></div>
                            {assertion.status}
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-center text-[#9ca3af] py-10">No assertions found for this test.</div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestView;
