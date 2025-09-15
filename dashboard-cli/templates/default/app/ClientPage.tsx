'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import RunList from '../components/RunList';
import ReportView from '../components/ReportView';

const ClientPage = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlRunId = searchParams.get('runId');

  const [selectedRun, setSelectedRun] = useState<string | null>(urlRunId);

  useEffect(() => {
    if (selectedRun && selectedRun !== urlRunId) {
      router.push(`/?runId=${selectedRun}`, { scroll: false });
    } else if (!selectedRun && urlRunId) {
      router.push('/', { scroll: false });
    }
  }, [selectedRun, urlRunId, router]);

  useEffect(() => {
    if (urlRunId && !selectedRun) {
      setSelectedRun(urlRunId);
    }
  }, [urlRunId, selectedRun]);


  const handleSelectRun = (runId: string) => {
    setSelectedRun(runId);
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

export default ClientPage;
