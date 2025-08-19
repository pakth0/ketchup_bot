import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const { dataUrl } = (await request.json()) as { dataUrl?: string };
    if (!dataUrl || !dataUrl.startsWith("data:")) {
      return NextResponse.json({ error: "Invalid dataUrl" }, { status: 400 });
    }

    const commaIndex = dataUrl.indexOf(",");
    const meta = dataUrl.slice(5, commaIndex); // e.g. image/jpeg;base64
    const base64 = dataUrl.slice(commaIndex + 1);
    const extension = meta.includes("image/png") ? "png" : "jpg";
    const buffer = Buffer.from(base64, "base64");

    const uploadsDir = path.join(process.cwd(), "public", "uploads");
    await fs.mkdir(uploadsDir, { recursive: true });
    const filename = `${Date.now()}-${Math.random().toString(36).slice(2)}.${extension}`;
    const filePath = path.join(uploadsDir, filename);
    await fs.writeFile(filePath, buffer);

    const urlPath = `/uploads/${filename}`;
    return NextResponse.json({ url: urlPath });
  } catch (error) {
    return NextResponse.json({ error: "Upload failed" }, { status: 500 });
  }
}




