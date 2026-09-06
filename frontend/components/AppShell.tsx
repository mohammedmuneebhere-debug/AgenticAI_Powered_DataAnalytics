"use client";

import { SocialIQProvider } from "@/context/SocialIQContext";
import SocialIQLayout from "./shell/SocialIQLayout";

export default function AppShell() {
  return (
    <SocialIQProvider>
      <SocialIQLayout />
    </SocialIQProvider>
  );
}
