"use client";

import React from "react";

export type MenuItem = {
  id: string;
  name: string;
  description?: string;
  priceCents: number;
};

type MenuItemCardProps = {
  item: MenuItem;
  onAddToCart: (item: MenuItem) => void;
};

function formatMoneyFromCents(cents: number): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(cents / 100);
}

export default function MenuItemCard({ item, onAddToCart }: MenuItemCardProps) {
  return (
    <button
      type="button"
      onClick={() => onAddToCart(item)}
      className="rounded-2xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-6 text-left shadow-sm transition-colors select-none"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold leading-tight">{item.name}</h3>
          {item.description ? (
            <p className="text-sm/6 text-white/90 mt-1">{item.description}</p>
          ) : null}
        </div>
        <div className="text-lg font-bold whitespace-nowrap">
          {formatMoneyFromCents(item.priceCents)}
        </div>
      </div>
      <div className="mt-3 text-sm opacity-90">Tap to add</div>
    </button>
  );
}


