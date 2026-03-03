"use client";

import { useParams } from "next/navigation";
import ProfilePage from "../page";

// Re-use the same profile page component, it handles username param internally
export default function ProfileUserPage() {
  return <ProfilePage />;
}
