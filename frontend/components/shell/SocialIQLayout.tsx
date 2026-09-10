"use client";

import React from "react";
import { useSocialIQ } from "@/context/SocialIQContext";
import TopNavigation from "./TopNavigation";
import ToolsConnectorsSidebar from "./ToolsConnectorsSidebar";
import ConversationSidebar from "./ConversationSidebar";
import ChatMode from "../chat/ChatMode";
import DashboardMode from "../dashboard/DashboardMode";

export default function SocialIQLayout() {
  const { activeMode } = useSocialIQ();

  return (
    <div className="min-h-screen bg-[var(--bg-app)] text-on-surface antialiased flex flex-col">
      {/* Top Navigation */}
      <TopNavigation />

      {/* Main Workspace + Persistent Sidebar */}
      <div className="flex w-full pt-16 flex-1">
        <ConversationSidebar />
        {/* Main Content Area: Chat or Dashboard (Never both simultaneously) */}
        <main className="flex-1 min-h-[calc(100vh-4rem)] bg-[var(--bg-app)] p-4 sm:p-6 overflow-y-auto">
          {activeMode === "chat" ? <ChatMode /> : <DashboardMode />}
        </main>

        {/* Persistent Tools & Connectors Sidebar (Available in both modes) */}
        <ToolsConnectorsSidebar />
      </div>
    </div>
  );
}
