"use client";

import { useState } from "react";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);

  function handleSearch() {
    fetch(`http://127.0.0.1:8000/analyses/search?query=${query}`)
      .then((response) => response.json())
      .then((data) => setResults(data));
  }

  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold">Search Startups</h1>

      <p className="mt-4 text-gray-400">
        Search startups in the intelligence engine.
      </p>

      <div className="mt-8 flex gap-4">
        <input
          className="w-full rounded-lg bg-gray-900 border-gray-800 p-3 text-white"
          placeholder="Search by company, summary, market, risk..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />

        <button
          onClick={handleSearch}
          className="rounded-lg bg-blue-600 px-6 font-semibold hover:bg-blue-500"
        >
          Search
        </button>
      </div>

      <div className="=mt-8 space-y-4">
        {results.map((startup, index) => (
          <div
            key={index}
            className="rounded-xl bg-gray-900 p-6 border border-gray-800"
          >
            <h2 className="text-2xl font-bold">
              {startup.company_name ?? "Unknown Startup"}
            </h2>

            <p className="mt-2 text-gray-400">{startup.summary}</p>

            <p className="mt-4">
              Overall Score: {startup.overall_score ?? "--"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
