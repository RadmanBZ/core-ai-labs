import { NextRequest, NextResponse } from "next/server";

import { getLiveBridgeState, setLiveBridgeState } from "@/lib/telemetry-store";
import { TelemetryBridgePayload } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  const payload = await getLiveBridgeState();
  return NextResponse.json(payload, {
    headers: {
      "Cache-Control": "no-store, max-age=0",
    },
  });
}

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as TelemetryBridgePayload;
    setLiveBridgeState(payload);
    return NextResponse.json({ ok: true, updated_at: payload.updated_at });
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid telemetry payload" }, { status: 400 });
  }
}
