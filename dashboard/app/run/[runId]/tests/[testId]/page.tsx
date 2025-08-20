'use client';

import TestView from '@/components/TestView';
import { use } from 'react';

const TestPage = ({ params }: { params: Promise<{ runId: string, testId: string }> }) => {
  const { testId, runId } = use(params)
  return (
    <div className="container mx-auto">
      <TestView runId={runId} testId={testId} />
    </div>
  );
};

export default TestPage;