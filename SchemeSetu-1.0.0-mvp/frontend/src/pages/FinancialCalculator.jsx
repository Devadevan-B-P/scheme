import { useState, useMemo } from 'react'
import { Calculator, ArrowRight, AlertTriangle, Info, PieChart, Landmark } from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function FinancialCalculator() {
  const { calculatorInput, updateCalculatorInput, selectedScheme, setActiveTab } = useChatStore()

  // State inputs
  const [loanAmount, setLoanAmount] = useState(calculatorInput.loanAmount || 450000)
  const [interestRate, setInterestRate] = useState(calculatorInput.interestRate || 6.0)
  const [tenureYears, setTenureYears] = useState(calculatorInput.tenureYears || 5)
  const [moratoriumMonths, setMoratoriumMonths] = useState(calculatorInput.moratoriumMonths || 6)
  const [ownContribution, setOwnContribution] = useState(calculatorInput.ownContribution || 50000)

  // Calculations
  const results = useMemo(() => {
    const totalProjectCost = Number(loanAmount) + Number(ownContribution)
    const principal = Number(loanAmount)
    const rate = Number(interestRate) / 100 / 12
    const totalMonths = Number(tenureYears) * 12

    let emi = 0
    let totalRepayment = 0
    let totalInterest = 0

    if (principal > 0 && rate > 0 && totalMonths > 0) {
      emi = Math.round(
        (principal * rate * Math.pow(1 + rate, totalMonths)) /
          (Math.pow(1 + rate, totalMonths) - 1)
      )
      totalRepayment = emi * totalMonths
      totalInterest = Math.max(0, totalRepayment - principal)
    }

    return {
      totalProjectCost,
      principal,
      emi,
      totalInterest,
      totalRepayment,
    }
  }, [loanAmount, interestRate, tenureYears, ownContribution])

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-2">
            <Landmark size={14} />
            <span>Scheme Parameter Simulator</span>
          </div>
          <h1 className="text-xl md:text-2xl font-black text-white">Financial & EMI Calculator</h1>
          <p className="text-xs text-slate-400">
            Simulate loan repayments, interest rates, and own contribution requirements for {selectedScheme ? selectedScheme.name : 'government schemes'}.
          </p>
        </div>

        {selectedScheme && (
          <div className="shrink-0 p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 text-xs space-y-1">
            <span className="text-slate-400">Pre-configured Scheme:</span>
            <p className="font-bold text-indigo-300">{selectedScheme.name}</p>
          </div>
        )}
      </div>

      {/* Main Grid: Inputs vs Results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Inputs (7 Cols) */}
        <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-5">
          <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">Loan Inputs</h3>

          {/* Loan Amount Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <label className="font-semibold text-slate-300">Loan Amount (Principal)</label>
              <span className="font-mono font-bold text-indigo-400">₹{Number(loanAmount).toLocaleString('en-IN')}</span>
            </div>
            <input
              type="range"
              min={50000}
              max={1500000}
              step={25000}
              value={loanAmount}
              onChange={(e) => setLoanAmount(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>₹50,000</span>
              <span>₹15,000,000</span>
            </div>
          </div>

          {/* Own Contribution */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <label className="font-semibold text-slate-300">Own Contribution (Margin Money)</label>
              <span className="font-mono font-bold text-emerald-400">₹{Number(ownContribution).toLocaleString('en-IN')}</span>
            </div>
            <input
              type="range"
              min={0}
              max={250000}
              step={10000}
              value={ownContribution}
              onChange={(e) => setOwnContribution(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>

          {/* Interest Rate & Tenure Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Interest Rate (% p.a.)</label>
              <input
                type="number"
                step="0.5"
                value={interestRate}
                onChange={(e) => setInterestRate(Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Tenure (Years)</label>
              <input
                type="number"
                value={tenureYears}
                onChange={(e) => setTenureYears(Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Moratorium (Months)</label>
              <input
                type="number"
                value={moratoriumMonths}
                onChange={(e) => setMoratoriumMonths(Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Visualization Flow */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Project Funding Flow</span>
            <div className="grid grid-cols-4 gap-2 text-center text-xs">
              <div className="p-2.5 rounded-xl bg-slate-800 border border-slate-700 space-y-1">
                <span className="text-[9px] text-slate-400 block">Project Cost</span>
                <span className="font-extrabold text-slate-100 text-[11px]">₹{(results.totalProjectCost / 100000).toFixed(2)}L</span>
              </div>
              <div className="p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-800/40 space-y-1">
                <span className="text-[9px] text-emerald-300 block">Own Contrib.</span>
                <span className="font-extrabold text-emerald-400 text-[11px]">₹{(ownContribution / 100000).toFixed(2)}L</span>
              </div>
              <div className="p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-800/40 space-y-1">
                <span className="text-[9px] text-indigo-300 block">Net Loan</span>
                <span className="font-extrabold text-indigo-300 text-[11px]">₹{(loanAmount / 100000).toFixed(2)}L</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-800 border border-slate-700 space-y-1">
                <span className="text-[9px] text-slate-400 block">Est. EMI</span>
                <span className="font-extrabold text-white text-[11px]">₹{results.emi.toLocaleString('en-IN')}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Output Cards (5 Cols) */}
        <div className="lg:col-span-5 space-y-5">
          <div className="bg-gradient-to-br from-indigo-950/70 via-slate-900 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 space-y-5">
            <h3 className="text-base font-bold text-white border-b border-slate-800/80 pb-3">Repayment Summary</h3>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-center space-y-1">
                <span className="text-xs text-indigo-300 font-semibold uppercase">Estimated Monthly Installment (EMI)</span>
                <div className="text-3xl font-black text-white">₹{results.emi.toLocaleString('en-IN')} <span className="text-xs font-normal text-slate-400">/ mo</span></div>
              </div>

              <div className="space-y-2.5 pt-2 text-xs">
                <div className="flex justify-between p-3 rounded-xl bg-slate-800/60 border border-slate-700/50">
                  <span className="text-slate-400">Total Interest Payable:</span>
                  <span className="font-bold text-indigo-300">₹{results.totalInterest.toLocaleString('en-IN')}</span>
                </div>

                <div className="flex justify-between p-3 rounded-xl bg-slate-800/60 border border-slate-700/50">
                  <span className="text-slate-400">Total Repayment Amount:</span>
                  <span className="font-bold text-white">₹{results.totalRepayment.toLocaleString('en-IN')}</span>
                </div>

                <div className="flex justify-between p-3 rounded-xl bg-slate-800/60 border border-slate-700/50">
                  <span className="text-slate-400">Moratorium Grace Period:</span>
                  <span className="font-bold text-emerald-400">{moratoriumMonths} Months</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => setActiveTab('partner-finder')}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 transition-colors shadow-lg shadow-indigo-600/25"
            >
              <span>Apply via Channel Partner</span>
              <ArrowRight size={16} />
            </button>
          </div>

          {/* Disclaimer Box */}
          <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/30 text-amber-300/90 text-xs space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-amber-400">
              <AlertTriangle size={15} />
              <span>Institutional Disclaimer</span>
            </div>
            <p className="text-[11px] leading-relaxed text-amber-200/80">
              ⚠️ Estimates are based on the scheme parameters and may vary according to the lending institution, processing fees, and margin money regulations.
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}
