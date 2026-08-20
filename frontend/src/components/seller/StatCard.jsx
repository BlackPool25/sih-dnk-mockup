function StatCard({ title, value }) {
  return (
    <div className="rounded-xl border border-[#E1E7DF] bg-white px-5 py-4">
      <p className="font-['Figtree'] text-[12px] text-[#687268]">
        {title}
      </p>

      <p className="mt-2 font-['Fraunces'] text-[30px] font-semibold text-[#1B2E1B]">
        {value}
      </p>
    </div>
  )
}

export default StatCard