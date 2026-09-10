"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ThemeProvider } from "@/context/ThemeContext";
import { SocialIQProvider } from "@/context/SocialIQContext";
import SocialIQLayout from "./shell/SocialIQLayout";
import { getToken, fetchCurrentUser, clearSession } from "@/lib/auth";

export default function AppShell() {
  const router = useRouter();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser(token)
      .then(() => setAuthed(true))
      .catch(() => {
        clearSession();
        router.replace("/login");
      });
  }, [router]);

  return (
    <ThemeProvider>
      {authed ? (
        <SocialIQProvider>
          <SocialIQLayout />
        </SocialIQProvider>
      ) : (
        <div className="min-h-screen bg-[var(--bg-app)] flex items-center justify-center">
          <span className="material-symbols-outlined text-[28px] text-[var(--text-muted)] animate-spin">
            progress_activity
          </span>
        </div>
      )}
    </ThemeProvider>
  );
}
