"use client";

import React from "react";
import type { MenuItem } from "./MenuItemCard";

export type CartItem = MenuItem & { quantity: number };

type CartProps = {
  items: CartItem[];
  onIncrement: (id: string) => void;
  onDecrement: (id: string) => void;
  onRemove: (id: string) => void;
};

function formatMoneyFromCents(cents: number): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(cents / 100);
}

export default function Cart({ items, onIncrement, onDecrement, onRemove }: CartProps) {
  const subtotalCents = items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);

  return (
    <div className="rounded-2xl bg-white shadow-sm border border-black/10 p-5">
      <h2 className="text-2xl font-semibold mb-4">Your order</h2>
      {items.length === 0 ? (
        <p className="text-base text-black/60">Your cart is empty.</p>
      ) : (
        <div className="flex flex-col gap-4">
          <ul className="flex flex-col gap-3">
            {items.map((item) => (
              <li key={item.id} className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-medium truncate text-lg">{item.name}</p>
                  <p className="text-sm text-black/60">
                    {formatMoneyFromCents(item.priceCents)} × {item.quantity}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => onDecrement(item.id)}
                    className="h-10 w-10 inline-flex items-center justify-center rounded-md border border-black/10 text-lg"
                    aria-label={`Decrease ${item.name}`}
                  >
                    −
                  </button>
                  <span className="w-8 text-center tabular-nums text-lg">{item.quantity}</span>
                  <button
                    type="button"
                    onClick={() => onIncrement(item.id)}
                    className="h-10 w-10 inline-flex items-center justify-center rounded-md border border-black/10 text-lg"
                    aria-label={`Increase ${item.name}`}
                  >
                    +
                  </button>
                  <button
                    type="button"
                    onClick={() => onRemove(item.id)}
                    className="ml-2 text-sm text-red-600 hover:underline"
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <div className="pt-3 border-t border-black/10 flex items-center justify-between">
            <span className="text-base text-black/70">Subtotal</span>
            <span className="font-semibold text-lg">{formatMoneyFromCents(subtotalCents)}</span>
          </div>
        </div>
      )}
    </div>
  );
}


