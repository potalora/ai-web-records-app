import { redirect } from "next/navigation"

export default function Home() {
  // Redirect to overview (main landing page)
  redirect("/overview")
}
