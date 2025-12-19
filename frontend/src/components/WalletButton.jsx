import { useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";

export function WalletButton() {
  return (
    <WalletMultiButton
      data-testid="wallet-connect-button"
      style={{
        backgroundColor: "#1D6FFF",
        borderRadius: "9999px",
        fontSize: "14px",
        fontWeight: "600",
        padding: "12px 24px",
        transition: "all 0.2s",
      }}
    />
  );
}