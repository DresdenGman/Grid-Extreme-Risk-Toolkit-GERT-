export default function About() {
  return (
    <div className="max-w-3xl mx-auto prose prose-invert">
      <h1>Methodology</h1>
      <p className="text-lg text-slate-300">
        The Grid Extreme Risk Toolkit (GERT) uses <strong>Quantile Regression</strong> to model the uncertainty in electricity demand.
      </p>

      <h3>Why not standard regression?</h3>
      <p>
        Standard regression predicts the <em>average</em> (mean) outcome. In grid reliability, we don't care about the average day; 
        we care about the 1-in-10-year event that causes blackouts.
      </p>

      <h3>Key Metrics</h3>
      <ul className="list-disc pl-5 space-y-2 text-slate-300">
        <li><strong>P50 (Median):</strong> The expected load.</li>
        <li><strong>P99 (Extreme Tail):</strong> There is only a 1% chance load exceeds this value.</li>
        <li><strong>Risk Score:</strong> A normalized metric (0-100) derived from the distance between P99 and Generation Capacity.</li>
      </ul>

      <div className="bg-slate-800 p-6 rounded-lg mt-8 border border-slate-700">
        <h4 className="text-yellow-400 font-bold mb-2">Disclaimer</h4>
        <p className="text-sm m-0">
          This tool is a Minimal Viable Product (MVP) for demonstration purposes. 
          It provides probabilistic forecasts based on synthetic or stubbed data. 
          It does not guarantee grid stability and should not be used for actual grid operations without real data integration.
        </p>
      </div>
    </div>
  );
}