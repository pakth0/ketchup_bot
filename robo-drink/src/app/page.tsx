"use client";

import React, { useMemo, useState } from "react";
import MenuItemCard, { type MenuItem } from "@/components/MenuItemCard";
import Cart, { type CartItem } from "@/components/Cart";
import TipSelector from "@/components/TipSelector";
import SuccessScreen from "@/components/SuccessScreen";
import ApiControls from "@/components/ApiControls";

const MENU_ITEMS: MenuItem[] = [
  { id: "latte", name: "Latte", description: "Espresso, steamed milk", priceCents: 495 },
  { id: "cappuccino", name: "Cappuccino", description: "Espresso, foam", priceCents: 475 },
  { id: "americano", name: "Americano", description: "Espresso, hot water", priceCents: 350 },
  { id: "mocha", name: "Mocha", description: "Espresso, chocolate, milk", priceCents: 525 },
  { id: "tea", name: "Hot Tea", description: "Assorted teas", priceCents: 300 },
  { id: "lemonade", name: "Lemonade", description: "Fresh squeezed", priceCents: 350 },
];

export default function Home() {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [isTipOpen, setIsTipOpen] = useState(false);
  const [isSuccessOpen, setIsSuccessOpen] = useState(false);

  const subtotalCents = useMemo(
    () => cart.reduce((sum, item) => sum + item.priceCents * item.quantity, 0),
    [cart]
  );

  function handleAddToCart(item: MenuItem) {
    setCart((prev) => {
      const existing = prev.find((ci) => ci.id === item.id);
      if (existing) {
        return prev.map((ci) => (ci.id === item.id ? { ...ci, quantity: ci.quantity + 1 } : ci));
      }
      return [...prev, { ...item, quantity: 1 }];
    });
  }

  function handleIncrement(id: string) {
    setCart((prev) => prev.map((ci) => (ci.id === id ? { ...ci, quantity: ci.quantity + 1 } : ci)));
  }

  function handleDecrement(id: string) {
    setCart((prev) =>
      prev
        .map((ci) => (ci.id === id ? { ...ci, quantity: Math.max(0, ci.quantity - 1) } : ci))
        .filter((ci) => ci.quantity > 0)
    );
  }

  function handleRemove(id: string) {
    setCart((prev) => prev.filter((ci) => ci.id !== id));
  }

  function handleCheckout() {
    if (cart.length === 0) return;
    setIsTipOpen(true);
  }

  function handleTipConfirm(tipCentsParam: number) {
    try { window.sessionStorage.setItem("lastTipCents", String(tipCentsParam)); } catch {}
    setIsTipOpen(false);
    setIsSuccessOpen(true);
  }

  function handleSuccessClose() {
    setIsSuccessOpen(false);
    setCart([]);
  }

  return (
    <div className="min-h-screen w-full px-6 py-8">
      <header className="max-w-6xl mx-auto w-full flex items-center justify-between mb-6">
        <h1 className="text-3xl font-semibold">Robo Drinks</h1>
        <div className="text-base text-black/60">Kiosk ordering</div>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {MENU_ITEMS.map((item) => (
            <MenuItemCard key={item.id} item={item} onAddToCart={handleAddToCart} />
          ))}
        </section>

        <aside className="lg:col-span-1 flex flex-col gap-4">
          <Cart
            items={cart}
            onIncrement={handleIncrement}
            onDecrement={handleDecrement}
            onRemove={handleRemove}
          />
          <button
            type="button"
            onClick={handleCheckout}
            className="rounded-2xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-4 text-lg font-semibold disabled:opacity-50"
            disabled={cart.length === 0}
          >
            Checkout
          </button>
        </aside>
      </main>

      <TipSelector
        subtotalCents={subtotalCents}
        isOpen={isTipOpen}
        onClose={() => setIsTipOpen(false)}
        onConfirm={handleTipConfirm}
      />

      <SuccessScreen isOpen={isSuccessOpen} onClose={handleSuccessClose} />
      
      {/* Fixed positioned API controls in bottom right corner - only show on main screen */}
      {!isTipOpen && !isSuccessOpen && (
        <div className="fixed bottom-4 right-4 z-50">
          <ApiControls />
        </div>
      )}
    </div>
  );
}
