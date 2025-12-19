import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SolanaProvider } from "@/lib/SolanaProvider";
import { CurrencyProvider } from "@/contexts/CurrencyContext";
import { Toaster } from "sonner";
import HomePage from "@/pages/HomePage";
import SwapPage from "@/pages/SwapPage";
import DashboardPage from "@/pages/DashboardPage";

function App() {
  return (
    <SolanaProvider>
      <CurrencyProvider>
        <div className="App min-h-screen bg-[#020408]">
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/swap" element={<SwapPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
            </Routes>
          </BrowserRouter>
          <Toaster 
            position="top-right"
            toastOptions={{
              style: {
                background: "rgba(11, 12, 18, 0.95)",
                color: "#fff",
                border: "1px solid rgba(255, 255, 255, 0.1)",
              },
            }}
          />
        </div>
      </CurrencyProvider>
    </SolanaProvider>
  );
}

export default App;