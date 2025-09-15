import { Suspense } from 'react';
import ClientPage from './ClientPage';

const Page = () => {
  return (
    <Suspense>
      <ClientPage />
    </Suspense>
  );
};

export default Page;