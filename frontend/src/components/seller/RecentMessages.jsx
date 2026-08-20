// src/components/RecentMessages.jsx
import { ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

const messages = [
  {
    name: "Priya Sharma",
    initial: "P",
    preview: "Can I get this shipped to...",
    time: "2 min ago",
  },
  {
    name: "Rahul Mehta",
    initial: "R",
    preview: "Is this product available?",
    time: "15 min ago",
  },
  {
    name: "Ananya Rao",
    initial: "A",
    preview: "I'd like to know more...",
    time: "1 hr ago",
  },
];

// 🎨 Different colors for each avatar
const avatarColors = {
  "Priya Sharma": "bg-emerald-100 text-emerald-700",
  "Rahul Mehta": "bg-blue-100 text-blue-700",
  "Ananya Rao": "bg-purple-100 text-purple-700",
};

function RecentMessages() {
    const navigate = useNavigate();
  return (
    <div className="rounded-xl border border-[#E1E7DF] bg-white p-6">
      {/* Header with View All button */}
      <div className="flex items-center justify-between">
        <h2 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
          Recent Messages
        </h2>
        <button onClick={() => navigate("/messages")} className="flex items-center gap-1 font-['Figtree'] text-sm font-medium text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors">
          View all
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Messages List */}
      <div className="mt-5 space-y-0">
        {messages.map((message) => (
          <div
            key={message.name}
            className="flex items-center gap-3 border-b border-[#E8ECE7] py-3 last:border-0"
          >
            {/* Avatar with dynamic colors */}
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full font-['Figtree'] text-sm font-semibold ${avatarColors[message.name]}`}
            >
              {message.initial}
            </div>

            {/* Name + Preview */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                  {message.name}
                </p>
                <span className="shrink-0 font-['Figtree'] text-xs text-[#687268] ml-2">
                  {message.time}
                </span>
              </div>
              <p className="truncate font-['Figtree'] text-sm text-[#687268] mt-0.5">
                {message.preview}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RecentMessages;