import React from "react";

// --- HeroIcons SVGs for a professional look ---
const PaperAirplaneIcon = (props) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
  </svg>
);

const SparklesIcon = (props) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" >
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.898 20.502L16.5 21.75l-.398-1.248a3.375 3.375 0 00-2.455-2.456L12.75 18l1.248-.398a3.375 3.375 0 002.455-2.456L16.5 14.25l.398 1.248a3.375 3.375 0 002.456 2.456L20.25 18l-1.248.398a3.375 3.375 0 00-2.456 2.456z" />
    </svg>
);

// --- HELPER COMPONENTS ---

/*
 * Helper component for displaying a claim status in the chat.
 */
function ClaimStatusCard({ claim }) {
    const statusClasses = {
        'Under Review': 'text-yellow-700 bg-yellow-100 border-yellow-300',
        'Approved': 'text-green-700 bg-green-100 border-green-300',
        'Rejected': 'text-red-700 bg-red-100 border-red-300',
    };
    const classes = statusClasses[claim.status] || 'text-gray-600 bg-gray-100 border-gray-300';

    return (
        <div className="p-4 rounded-xl shadow-lg bg-white border border-gray-200">
            <div className="flex justify-between items-start mb-2">
                <p className="font-bold text-lg text-indigo-700">{claim.claimId}</p>
                <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${classes}`}>
                    {claim.status}
                </span>
            </div>
            <p className="text-sm text-gray-700 mb-1">Policy Holder: <span className="font-medium">{claim.policyHolder}</span></p>
            <p className="text-sm text-gray-700 mb-1">Amount: <span className="font-medium">₹{claim.amount.toLocaleString('en-IN')}</span></p>
            <p className="text-xs text-gray-500 mt-2 italic">Submitted: {claim.submittedOn}</p>
            <p className="text-xs text-gray-500 mt-1 italic">Notes: {claim.notes}</p>
        </div>
    );
}

// Re-factored MessageList to handle the new Claim type
function MessageList({ messages, isProcessing }) {
    return (
        <>
            {messages.map((m, i) => (
                <div key={i} className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                        className={`max-w-[75%] shadow-lg transition-all ${
                            m.from === "user"
                                ? "bg-indigo-600 text-white rounded-t-2xl rounded-l-2xl px-5 py-3"
                                : "bg-white text-gray-800 rounded-t-2xl rounded-r-2xl border border-gray-100"
                        }`}
                        // Conditional rendering for content: plain text or the ClaimStatusCard
                        style={m.type === 'claim' ? { padding: '0' } : { padding: '1.25rem' }} // Remove padding for the card
                    >
                        {m.type === 'claim' ? (
                            <ClaimStatusCard claim={m.claim} />
                        ) : (
                            m.text
                        )}
                    </div>
                </div>
            ))}
            {isProcessing && (
                <div className="flex justify-start">
                    <div className="px-5 py-3 rounded-2xl shadow-sm bg-white text-gray-500 rounded-bl-none">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-0"></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-150"></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-300"></div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

// --- MAIN APPLICATION COMPONENT ---
export default function App() {
    const sampleClaims = [
        { claimId: "CLM1001", policyHolder: "Amit Kumar", status: "Under Review", submittedOn: "2025-09-10", amount: 12500, notes: "Documents received, awaiting assessment" },
        { claimId: "CLM1002", policyHolder: "Rina Sharma", status: "Approved", submittedOn: "2025-08-18", amount: 43000, notes: "Settlement scheduled" },
        { claimId: "CLM1003", policyHolder: "Sahil Mehta", status: "Rejected", submittedOn: "2025-06-01", amount: 9800, notes: "Rejected due to missing documents" },
    ];
    
    const [messages, setMessages] = React.useState([
        { from: "agent", text: "Hi — I'm InsuraBot. How can I help you today? Try asking for the status of **CLM1001**.", type: "text" },
    ]);
    const [input, setInput] = React.useState("");
    const [claims] = React.useState(sampleClaims);
    const [isProcessing, setIsProcessing] = React.useState(false);
    const [escalations, setEscalations] = React.useState([]); // Kept for 'escalate' mock response

    const bottomRef = React.useRef(null);
    React.useEffect(() => {
        // Scrolls the chat to the bottom when new messages arrive
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isProcessing]);

    // Simple intent detection logic
    function detectIntent(text) {
        const t = text.toLowerCase();
        // Detects common phrases related to claim status and the CLM### format
        if (/(claim|status|claim id|claimid|clm)\s*[:#]?\s*[a-z0-9]/i.test(text)) return "claim_lookup";
        // Detects requests for a human agent
        if (/(agent|human|representative|talk to|escalate)/i.test(t)) return "escalate";
        return "general";
    }

    function extractClaimId(text) {
        // Extracts CLM followed by numbers, or just a 6+ digit number
        const match = text.match(/(CLM\d{3,}|clm\d{3,}|\b\d{6,}\b)/i);
        if (match) return match[0].toUpperCase();
        return null;
    }

    // AI response logic (calls backend API)
    async function sendToAI(userText) {
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText })
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            // Expected shape: { type: 'text', text: '...' }
            return data;
        } catch (e) {
            console.error(e);
            return { type: 'text', text: 'Backend error. Please ensure the API is running on :8000.' };
        }
    }

    async function handleSend(text = input) {
        const userText = text.trim();
        if (!userText) return;

        // 1. Add user message
        setMessages((m) => [...m, { from: "user", text: userText, type: "text" }]);
        setInput("");
        
        // 2. Show processing indicator
        setIsProcessing(true);
        
        try {
            // 3. Get AI response
            const response = await sendToAI(userText);
            // 4. Add AI response
            setMessages((m) => [...m, { from: "agent", ...response }]);
        } catch (err) {
            console.error(err);
            setMessages((m) => [...m, { from: "agent", text: "Sorry — an unexpected error occurred. Please try again.", type: "text" }]);
        } finally {
            // 5. Hide processing indicator
            setIsProcessing(false);
        }
    }

    // Centralized, standalone chat UI structure
    return (
        <div className="flex justify-center items-center h-screen w-full bg-gray-100 font-sans antialiased p-4">
            {/* Main Chat Card: Fixed width for focus, 90% height, centered */}
            <div className="w-full max-w-lg h-[90vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">
                {/* Header */}
                <header className="p-4 bg-indigo-600 text-white border-b border-indigo-700 shadow-lg">
                    <div className="flex items-center gap-3">
                         <SparklesIcon className="w-8 h-8 text-white" />
                         <div>
                            <h2 className="text-xl font-bold">InsuraBot Assistant</h2>
                            <p className="text-xs opacity-80">AI Insurance & Claim Support</p>
                         </div>
                    </div>
                </header>

                {/* Chat Messages Area */}
                <div className="flex-1 p-6 overflow-y-auto space-y-6">
                    <MessageList messages={messages} isProcessing={isProcessing} />
                    <div ref={bottomRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 bg-white border-t border-gray-100 shadow-t-lg">
                    <div className="relative">
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => { if (e.key === "Enter") handleSend(); }}
                            placeholder="Ask about claim status or request human assistance..."
                            className="w-full pl-5 pr-14 py-4 text-gray-700 bg-gray-100 border border-gray-200 rounded-3xl focus:outline-none focus:ring-4 focus:ring-indigo-100 transition shadow-inner text-base"
                            disabled={isProcessing}
                        />
                        <button
                            onClick={() => handleSend()}
                            disabled={isProcessing || !input.trim()}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-3 bg-indigo-600 text-white rounded-full disabled:bg-indigo-300 disabled:cursor-not-allowed hover:bg-indigo-700 transition-all shadow-md hover:shadow-lg focus:outline-none focus:ring-4 focus:ring-indigo-300"
                        >
                            <PaperAirplaneIcon className="w-6 h-6 transform rotate-45 -mt-1 -ml-1" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}