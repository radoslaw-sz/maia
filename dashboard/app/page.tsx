'use client';

import { useState, useEffect } from 'react'; // Add useEffect
import { useRouter, useSearchParams } from 'next/navigation'; // Import useRouter and useSearchParams
import RunList from '../components/RunList';
import ReportView from '../components/ReportView';

const Dashboard = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlRunId = searchParams.get('runId'); // Get runId from URL query parameter

  const [selectedRun, setSelectedRun] = useState<string | null>(urlRunId); // Initialize state from URL

  // Update URL when selectedRun changes (e.g., if user selects from RunList)
  useEffect(() => {
    if (selectedRun && selectedRun !== urlRunId) {
      router.push(`/?runId=${selectedRun}`, undefined, { shallow: true }); // Update URL without full page reload
    } else if (!selectedRun && urlRunId) {
      // If selectedRun becomes null but URL has runId, clear URL
      router.push('/', undefined, { shallow: true });
    }
  }, [selectedRun, urlRunId, router]);

  // Handle initial load or direct URL access
  useEffect(() => {
    if (urlRunId && !selectedRun) {
      setSelectedRun(urlRunId);
    }
  }, [urlRunId, selectedRun]);


  const handleSelectRun = (runId: string) => {
    setSelectedRun(runId); // This will trigger the useEffect to update the URL
  };

  return (
    <div className="flex h-screen bg-[#0f0f23]">
      <RunList onSelectRun={handleSelectRun} />
      <div className="flex-grow overflow-y-auto">
        {selectedRun ? (
          <ReportView runId={selectedRun} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500">Select a test run to view reports.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;