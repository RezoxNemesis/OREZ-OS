package com.orez.usb;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Optional, owner-enabled status reporting to the existing OREZ USB Studio relay.
 *
 * This Linux client is intentionally one-way: it posts a bounded status snapshot,
 * discards the response body, and has no API that returns or executes remote commands.
 * ISO contents, document URIs, serial numbers and unrelated phone files are never sent.
 */
public final class LiveMonitorClient implements AutoCloseable {
    public static final String BASE =
            "https://orez-usb-studio.prakasharuntandon634.workers.dev";

    private final String sessionId;
    private String token;

    public LiveMonitorClient(String pairingCode) throws IOException {
        if (pairingCode == null) throw new IOException("Pairing code is required.");
        String[] parts = pairingCode.trim().split("\\.", -1);
        if (parts.length != 2 ||
                !parts[0].matches("[0-9a-f]{32}") ||
                !parts[1].matches("[0-9a-f]{64}")) {
            throw new IOException("Paste the complete private pairing code supplied in this chat.");
        }
        sessionId = parts[0];
        token = parts[1];
    }

    public static boolean isValidCode(String pairingCode) {
        if (pairingCode == null) return false;
        String[] parts = pairingCode.trim().split("\\.", -1);
        return parts.length == 2 &&
                parts[0].matches("[0-9a-f]{32}") &&
                parts[1].matches("[0-9a-f]{64}");
    }

    public String shortSessionId() {
        return sessionId.substring(0, 8);
    }

    public synchronized void report(JSONObject status) throws IOException {
        if (token == null) throw new IOException("Live monitoring has been disconnected.");
        HttpURLConnection connection = (HttpURLConnection)
                new URL(BASE + "/api/control/" + sessionId).openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(15000);
        connection.setInstanceFollowRedirects(false);
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);
        connection.setRequestProperty("Authorization", "Bearer " + token);
        connection.setRequestProperty("Content-Type", "application/json");
        byte[] body = new JSONObject()
                .put("status", status)
                .put("ack", "")
                .toString().getBytes(StandardCharsets.UTF_8);
        connection.setFixedLengthStreamingMode(body.length);

        try {
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }
            int code = connection.getResponseCode();
            if (code != 200) {
                throw new IOException(code == 401 || code == 410
                        ? "Pairing code is invalid, revoked or expired. Request a fresh code."
                        : "Live reporting unavailable (HTTP " + code + "). Local USB work continues.");
            }
            // Drain and discard the response. In particular, never parse or execute
            // the legacy Windows endpoint's optional "command" field.
            try (InputStream input = connection.getInputStream();
                 ByteArrayOutputStream sink = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[1024];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    if (sink.size() + count > 16384) {
                        throw new IOException("Unexpectedly large monitor response.");
                    }
                    sink.write(buffer, 0, count);
                }
            }
        } finally {
            connection.disconnect();
        }
    }

    @Override public synchronized void close() {
        token = null;
    }
}
