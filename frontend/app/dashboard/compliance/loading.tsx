export default function ComplianceLoading() {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar skeleton */}
      <div className="hidden w-72 flex-col gap-4 border-r border-gray-200 p-4 dark:border-gray-700 lg:flex">
        <div className="h-8 w-40 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-10 w-full animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700" />
        <div className="mt-2 flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-14 w-full animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700"
            />
          ))}
        </div>
      </div>

      {/* Main content skeleton */}
      <div className="flex flex-1 flex-col gap-6 p-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="h-8 w-64 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="h-8 w-24 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        </div>

        {/* Stage content area */}
        <div className="flex-1 rounded-xl border border-gray-200 p-6 dark:border-gray-700">
          <div className="flex flex-col gap-4">
            <div className="h-6 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
            <div className="h-4 w-full animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
            <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
            <div className="mt-4 grid grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="h-32 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700"
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right stepper skeleton */}
      <div className="hidden w-56 flex-col gap-3 border-l border-gray-200 p-4 dark:border-gray-700 xl:flex">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="h-6 w-6 animate-pulse rounded-full bg-gray-200 dark:bg-gray-700" />
            <div className="h-4 w-28 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          </div>
        ))}
      </div>
    </div>
  );
}
