import Link from 'next/link';

const Sidebar = () => {
  return (
    <div className="w-64 h-screen p-5 flex-shrink-0 text-white">
      <h1 className="text-2xl font-bold mb-5">Maia Dashboard</h1>
      <ul>
        <li className="mb-2">
          <Link href="/" className="hover:text-gray-300">
            Runs
          </Link>
        </li>
      </ul>
    </div>
  );
};

export default Sidebar;
