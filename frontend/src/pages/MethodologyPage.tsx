export default function MethodologyPage() {
  return (
    <div className="max-w-3xl space-y-10">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Assessment Methodology</h2>
        <p className="text-sm text-gray-500 mt-1">How SecurityChecker scores and grades third-party software.</p>
      </div>

      {/* Overview */}
      <section className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
        <h3 className="text-lg font-semibold text-gray-900">Overview</h3>
        <p className="text-sm text-gray-700 leading-relaxed">
          Each assessment analyses a product across eight security domains using an AI model trained to evaluate
          publicly available information — vendor reputation, CVE history, repository activity, dependency
          health, encryption practices, logging posture, data exfiltration risk, and third-party integrations.
          Domain scores are combined into a weighted overall score (0–10) which maps to a RAG status and recommendation.
        </p>
      </section>

      {/* Scoring */}
      <section className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Scoring &amp; RAG Thresholds</h3>
        <p className="text-sm text-gray-700">Each module returns a score from 0–10. The overall score is a weighted average across all eight modules.</p>
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Overall Score</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">RAG</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Recommendation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr>
                <td className="px-4 py-3 text-gray-700">7.5 – 10.0</td>
                <td className="px-4 py-3"><span className="inline-flex items-center gap-1.5 text-green-700 font-medium"><span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" />Green</span></td>
                <td className="px-4 py-3 text-gray-700">Approve</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="px-4 py-3 text-gray-700">5.0 – 7.4</td>
                <td className="px-4 py-3"><span className="inline-flex items-center gap-1.5 text-amber-700 font-medium"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />Amber</span></td>
                <td className="px-4 py-3 text-gray-700">Conditional Approval</td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-gray-700">0.0 – 4.9</td>
                <td className="px-4 py-3"><span className="inline-flex items-center gap-1.5 text-red-700 font-medium"><span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />Red</span></td>
                <td className="px-4 py-3 text-gray-700">Reject</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Module weights */}
      <section className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Module Weights</h3>
        <p className="text-sm text-gray-700">Higher-weight modules have proportionally more influence on the overall score.</p>
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Module</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Weight</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[
                { module: 'CVE History', weight: '2.0', rationale: 'Scored on patch responsiveness, not raw CVE count. High-profile products with rapid patching score well; slow or unpatched vulnerabilities score poorly.' },
                { module: 'Maintenance', weight: '1.5', rationale: 'Unmaintained software cannot receive patches, compounding all other risks over time.' },
                { module: 'Dependency Risk', weight: '1.5', rationale: 'Vulnerable or abandoned dependencies are a primary supply-chain attack vector.' },
                { module: 'Encryption', weight: '1.5', rationale: 'Inadequate encryption directly exposes data in transit and at rest.' },
                { module: 'Data Exfiltration Risk', weight: '1.5', rationale: 'Unexpected outbound data flows present direct compliance and privacy risk.' },
                { module: 'Vendor Trust', weight: '1.0', rationale: 'Vendor reputation and transparency provide qualitative context.' },
                { module: 'Logging & Monitoring', weight: '1.0', rationale: 'Important for incident response but less immediately exploitable.' },
                { module: 'Third-Party Integrations', weight: '1.0', rationale: 'Adds attack surface but impact depends heavily on integration depth.' },
              ].map((row, i) => (
                <tr key={row.module} className={i % 2 === 1 ? 'bg-gray-50' : ''}>
                  <td className="px-4 py-3 font-medium text-gray-800">{row.module}</td>
                  <td className="px-4 py-3 text-gray-700">{row.weight}×</td>
                  <td className="px-4 py-3 text-gray-600">{row.rationale}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Standard vs Deep */}
      <section className="bg-white border border-gray-200 rounded-xl p-6 space-y-6">
        <h3 className="text-lg font-semibold text-gray-900">Standard vs Deep Review</h3>
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="text-sm font-semibold text-gray-700 border-b border-gray-200 pb-2">Standard</div>
            <ul className="text-sm text-gray-700 space-y-2">
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>One AI call per module (8 total)</li>
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>Single analyst perspective</li>
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>Suitable for initial screening and lower-risk products</li>
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>Faster — typically completes in minutes</li>
            </ul>
          </div>
          <div className="space-y-3">
            <div className="text-sm font-semibold text-gray-700 border-b border-gray-200 pb-2">Deep Review</div>
            <ul className="text-sm text-gray-700 space-y-2">
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>~11 AI calls per module (~88 total)</li>
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>Council of 5 independent advisors per module</li>
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>Advisors peer-review each other's findings</li>
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>Chairman synthesises into final verdict</li>
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>Reduces single-model bias and blind spots</li>
              <li className="flex gap-2"><span className="text-gray-400 mt-0.5">•</span>Recommended for high-risk or enterprise products</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Council advisors */}
      <section className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Deep Review: Council Advisors</h3>
        <p className="text-sm text-gray-700">Each module is independently evaluated by five advisors with distinct analytical lenses, followed by anonymous peer review and chairman synthesis.</p>
        <div className="space-y-3">
          {[
            { name: 'Security Purist', desc: 'Evaluates strictly against security best practices with no tolerance for risk trade-offs.' },
            { name: 'Pragmatic Engineer', desc: 'Considers real-world implementation context and whether findings are practically exploitable.' },
            { name: 'Compliance Officer', desc: 'Assesses against regulatory frameworks (GDPR, ISO 27001, SOC 2) and audit exposure.' },
            { name: 'Threat Modeller', desc: 'Constructs realistic attack scenarios and estimates likelihood and impact of exploitation.' },
            { name: 'Devil\'s Advocate', desc: 'Challenges the prevailing view — argues the opposite case to surface blind spots.' },
          ].map((a, i) => (
            <div key={a.name} className={`flex gap-4 p-3 rounded-lg ${i % 2 === 0 ? 'bg-gray-50' : ''}`}>
              <div className="w-36 shrink-0 text-sm font-semibold text-blue-800">{a.name}</div>
              <div className="text-sm text-gray-700">{a.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Limitations */}
      <section className="bg-amber-50 border border-amber-200 rounded-xl p-6 space-y-3">
        <h3 className="text-lg font-semibold text-amber-900">Limitations &amp; Caveats</h3>
        <ul className="text-sm text-amber-800 space-y-2">
          <li className="flex gap-2"><span className="mt-0.5">•</span>Assessments are based on publicly available information only — no penetration testing or source code audit is performed.</li>
          <li className="flex gap-2"><span className="mt-0.5">•</span>AI models may have knowledge cutoffs and may not reflect the latest CVEs, patches, or vendor changes.</li>
          <li className="flex gap-2"><span className="mt-0.5">•</span>Scores reflect relative risk posture, not absolute security guarantees.</li>
          <li className="flex gap-2"><span className="mt-0.5">•</span>Project scope context provided by the submitter influences grading — ensure it accurately represents the deployment environment.</li>
          <li className="flex gap-2"><span className="mt-0.5">•</span>Results should be used to inform — not replace — professional security review for critical deployments.</li>
        </ul>
      </section>
    </div>
  )
}
