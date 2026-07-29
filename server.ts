import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";

interface KeyRecord {
  key: string;
  expiry_date: string;
  registered_hwid: string | null;
  status: "ACTIVE" | "REVOKED";
  note: string;
}

// In-Memory Database for Key Verification
const keysDB: Record<string, KeyRecord> = {
  "PAK-VIP-9999-ULTIMATE": {
    key: "PAK-VIP-9999-ULTIMATE",
    expiry_date: "2028-12-31",
    registered_hwid: null, // Unbound, locks on first use
    status: "ACTIVE",
    note: "Master VIP License (Unbound)",
  },
  "PAK-TEST-2026-KEY1": {
    key: "PAK-TEST-2026-KEY1",
    expiry_date: "2027-06-30",
    registered_hwid: "FL-HWID-3A7F92B0C41E8D5A",
    status: "ACTIVE",
    note: "Bound Test Key",
  },
  "PAK-EXPIRED-KEY-00": {
    key: "PAK-EXPIRED-KEY-00",
    expiry_date: "2024-01-01",
    registered_hwid: null,
    status: "ACTIVE",
    note: "Expired Key for Testing",
  },
};

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // CORS Middleware
  app.use((req, res, next) => {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, User-Agent");
    if (req.method === "OPTIONS") {
      res.sendStatus(200);
      return;
    }
    next();
  });

  // --------------------------------------------------------------------------
  // API ENDPOINT: /api/verify (PHP verify.php Endpoint Emulation)
  // --------------------------------------------------------------------------
  app.post("/api/verify", (req, res) => {
    const key = (req.body.key || req.query.key || "").toString().trim();
    const hwid = (req.body.hwid || req.query.hwid || "").toString().trim();

    if (!key) {
      res.status(400).json({
        status: "INVALID",
        message: "License Key parameter is required.",
        timestamp: new Date().toISOString(),
      });
      return;
    }

    if (!hwid) {
      res.status(400).json({
        status: "INVALID",
        message: "Hardware ID (HWID) parameter is required.",
        timestamp: new Date().toISOString(),
      });
      return;
    }

    const record = keysDB[key];

    if (!record || record.status !== "ACTIVE") {
      res.json({
        status: "INVALID",
        message: "License Key does not exist or has been revoked.",
        timestamp: new Date().toISOString(),
      });
      return;
    }

    // Check Expiry Date
    const today = new Date();
    const expiry = new Date(record.expiry_date + "T23:59:59");

    if (today > expiry) {
      res.json({
        status: "EXPIRED",
        message: `License Key expired on ${record.expiry_date}`,
        timestamp: new Date().toISOString(),
        data: {
          key: record.key,
          expiry_date: record.expiry_date,
          days_remaining: 0,
        },
      });
      return;
    }

    const diffTime = Math.abs(expiry.getTime() - today.getTime());
    const daysRemaining = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    // Handle HWID Binding
    if (!record.registered_hwid) {
      // First activation -> Bind to HWID
      record.registered_hwid = hwid;
    } else if (record.registered_hwid !== hwid) {
      // Mismatch
      res.json({
        status: "DEVICE_MISMATCH",
        message: "Hardware ID mismatch. Key is locked to a different device.",
        timestamp: new Date().toISOString(),
        data: {
          key: record.key,
          your_hwid: hwid,
          registered_hwid: record.registered_hwid,
        },
      });
      return;
    }

    res.json({
      status: "SUCCESS",
      message: "Authentication successful. Access granted.",
      timestamp: new Date().toISOString(),
      data: {
        key: record.key,
        expiry_date: record.expiry_date,
        days_remaining: daysRemaining,
        registered_hwid: record.registered_hwid,
        hwid_matched: true,
      },
    });
  });

  // --------------------------------------------------------------------------
  // ADMIN API ROUTES FOR KEY MANAGEMENT
  // --------------------------------------------------------------------------
  app.get("/api/admin/keys", (req, res) => {
    const list = Object.values(keysDB).map((rec) => {
      const today = new Date();
      const expiry = new Date(rec.expiry_date + "T23:59:59");
      const isExpired = today > expiry;
      const days = isExpired
        ? 0
        : Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      return {
        ...rec,
        daysRemaining: days,
        isExpired,
      };
    });
    res.json(list);
  });

  app.post("/api/admin/keys/create", (req, res) => {
    const { key, daysValid, note } = req.body;
    if (!key) {
      res.status(400).json({ error: "Key string is required" });
      return;
    }
    const expiry = new Date();
    expiry.setDate(expiry.getDate() + (parseInt(daysValid, 10) || 30));
    const expiryStr = expiry.toISOString().split("T")[0];

    keysDB[key] = {
      key,
      expiry_date: expiryStr,
      registered_hwid: null,
      status: "ACTIVE",
      note: note || "Generated Key",
    };

    res.json({ success: true, key: keysDB[key] });
  });

  app.post("/api/admin/keys/reset-hwid", (req, res) => {
    const { key } = req.body;
    if (keysDB[key]) {
      keysDB[key].registered_hwid = null;
      res.json({ success: true, message: `HWID reset for key ${key}` });
    } else {
      res.status(404).json({ error: "Key not found" });
    }
  });

  app.post("/api/admin/keys/toggle-status", (req, res) => {
    const { key } = req.body;
    if (keysDB[key]) {
      keysDB[key].status = keysDB[key].status === "ACTIVE" ? "REVOKED" : "ACTIVE";
      res.json({ success: true, newStatus: keysDB[key].status });
    } else {
      res.status(404).json({ error: "Key not found" });
    }
  });

  // Vite Middleware Setup
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
