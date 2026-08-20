// src/components/RecentOrders.jsx
import { ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

const orders = [
  {
    id: "#1054",
    destination: "USA",
    status: "At DNK Counter",
  },
  {
    id: "#1053",
    destination: "Germany",
    status: "Packing",
  },
  {
    id: "#1052",
    destination: "UK",
    status: "Shipped",
  },
];

const statusStyles = {
  "At DNK Counter": "bg-amber-100 text-amber-700 border-amber-200",
  "Packing": "bg-blue-100 text-blue-700 border-blue-200",
  "Shipped": "bg-green-100 text-green-700 border-green-200",
};

function RecentOrders() {
    const navigate = useNavigate();
  return (
    <div className="rounded-xl border border-[#E1E7DF] bg-white p-6">
      <div className="flex items-center justify-between">
        <h2 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
          Recent Orders
        </h2>
        <button onClick={() => navigate("/orders")} className="flex items-center gap-1 font-['Figtree'] text-sm font-medium text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors">
          View all
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      <div className="mt-5 space-y-0">
        {orders.map((order) => (
          <div
            key={order.id}
            className="flex items-center justify-between border-b border-[#E8ECE7] py-3 last:border-0"
          >
            <div className="flex items-center gap-3">
              <span className="font-['Figtree'] font-medium text-[#1B2E1B]">
                {order.id}
              </span>
              <span className="font-['Figtree'] text-sm text-[#687268]">
                {order.destination}
              </span>
            </div>

            <span
              className={`px-3 py-1 text-xs font-medium font-['Figtree'] rounded-full border ${statusStyles[order.status]}`}
            >
              {order.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RecentOrders;