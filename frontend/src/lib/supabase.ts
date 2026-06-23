import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "http://localhost:54321";
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || "dummy-key";

/**
 * Browser-side Supabase client.
 * Use this in Client Components ("use client").
 */
export const supabase = createBrowserClient(supabaseUrl, supabaseKey);
