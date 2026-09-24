package com.glmgame.fps;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;

/**
 * Tiny embedded HTTP server that serves the game through a StreamSource on
 * http://127.0.0.1:<port>. Serving over a real HTTP origin (instead of
 * file://) keeps WebView localStorage, texture loading and audio behaviour
 * consistent on every Android version. The port is FIXED (with a small
 * fallback chain) so the origin never changes and saved settings survive
 * app restarts and game updates.
 *
 * Pure java.net code - unit-testable on the desktop JVM.
 */
public class GameServer {

    /** Provides game files by relative path (e.g. "fps-game.html"). Null = missing. */
    public interface StreamSource {
        InputStream open(String path) throws IOException;
    }

    private final StreamSource src;
    private final ServerSocket socket;
    private volatile boolean running = true;

    public GameServer(StreamSource src, int preferredPort) throws IOException {
        this.src = src;
        ServerSocket ss = null;
        IOException last = null;
        int port = preferredPort;
        for (int i = 0; i < 10; i++) { // 8777..8786 fallback chain (rarely needed)
            try {
                ss = new ServerSocket(port, 64, InetAddress.getByName("127.0.0.1"));
                break;
            } catch (IOException e) {
                last = e;
                port++;
            }
        }
        if (ss == null) throw last;
        this.socket = ss;
    }

    public int getPort() { return socket.getLocalPort(); }

    public void start() {
        Thread t = new Thread(new Runnable() { public void run() { loop(); } }, "GameServer");
        t.setDaemon(true);
        t.start();
    }

    public void stop() {
        running = false;
        try { socket.close(); } catch (IOException ignored) {}
    }

    private void loop() {
        while (running) {
            try {
                final Socket s = socket.accept();
                s.setSoTimeout(8000);
                Thread req = new Thread(new Runnable() { public void run() { handle(s); } }, "gs-req");
                req.setDaemon(true);
                req.start();
            } catch (IOException e) {
                if (!running) return;
                sleep(50);
            }
        }
    }

    private void handle(Socket s) {
        try {
            InputStream in = new BufferedInputStream(s.getInputStream());
            OutputStream out = new BufferedOutputStream(s.getOutputStream());
            String requestLine = readLine(in);
            if (requestLine == null || requestLine.isEmpty()) return;
            // drain request headers
            String h;
            while ((h = readLine(in)) != null && !h.isEmpty()) { /* drain */ }

            String path = extractPath(requestLine);
            if (path == null) { sendSimple(out, 400, "bad request"); return; }
            path = normalize(path);
            if (path == null) { sendSimple(out, 403, "forbidden"); return; }
            if (path.equals("/")) path = "/fps-game.html";

            InputStream is = src.open(path.substring(1));
            if (is == null) { sendSimple(out, 404, "not found"); return; }
            byte[] body = readAll(is);
            try { is.close(); } catch (IOException ignored) {}

            String head = "HTTP/1.1 200 OK\r\n"
                    + "Content-Type: " + mimeOf(path) + "\r\n"
                    + "Content-Length: " + body.length + "\r\n"
                    + "Cache-Control: no-cache\r\n"
                    + "Access-Control-Allow-Origin: *\r\n"
                    + "Connection: close\r\n\r\n";
            out.write(head.getBytes(StandardCharsets.US_ASCII));
            out.write(body);
            out.flush();
        } catch (Exception e) {
            // best effort: a dropped request must never crash the server thread
        } finally {
            try { s.close(); } catch (IOException ignored) {}
        }
    }

    private static String extractPath(String requestLine) {
        String[] parts = requestLine.split(" ");
        if (parts.length < 2) return null;
        String m = parts[0].toUpperCase();
        if (!m.equals("GET") && !m.equals("HEAD")) return null;
        return parts[1];
    }

    /** Strips query/fragment, URL-decodes, rejects traversal. Null = rejected. */
    static String normalize(String raw) {
        try {
            int q = raw.indexOf('?');
            if (q >= 0) raw = raw.substring(0, q);
            int f = raw.indexOf('#');
            if (f >= 0) raw = raw.substring(0, f);
            String p = URLDecoder.decode(raw, "UTF-8").replace('\\', '/');
            if (!p.startsWith("/")) return null;
            if (p.contains("\0")) return null;
            String[] segs = p.split("/");
            StringBuilder sb = new StringBuilder();
            for (String seg : segs) {
                if (seg.isEmpty() || seg.equals(".")) continue;
                if (seg.equals("..")) return null; // no traversal, ever
                sb.append('/').append(seg);
            }
            if (sb.length() == 0) return "/";
            return sb.toString();
        } catch (Exception e) {
            return null;
        }
    }

    static String mimeOf(String path) {
        String p = path.toLowerCase();
        if (p.endsWith(".html") || p.endsWith(".htm")) return "text/html; charset=utf-8";
        if (p.endsWith(".js")) return "application/javascript";
        if (p.endsWith(".json")) return "application/json";
        if (p.endsWith(".png")) return "image/png";
        if (p.endsWith(".jpg") || p.endsWith(".jpeg")) return "image/jpeg";
        if (p.endsWith(".gif")) return "image/gif";
        if (p.endsWith(".svg")) return "image/svg+xml";
        if (p.endsWith(".ico")) return "image/x-icon";
        if (p.endsWith(".css")) return "text/css; charset=utf-8";
        if (p.endsWith(".wav")) return "audio/wav";
        if (p.endsWith(".mp3")) return "audio/mpeg";
        if (p.endsWith(".ogg")) return "audio/ogg";
        if (p.endsWith(".m4a")) return "audio/mp4";
        if (p.endsWith(".woff")) return "font/woff";
        if (p.endsWith(".woff2")) return "font/woff2";
        if (p.endsWith(".txt")) return "text/plain; charset=utf-8";
        return "application/octet-stream";
    }

    private static void sendSimple(OutputStream out, int code, String msg) throws IOException {
        byte[] body = msg.getBytes(StandardCharsets.US_ASCII);
        String head = "HTTP/1.1 " + code + (code == 404 ? " Not Found" : code == 403 ? " Forbidden" : " Error")
                + "\r\nContent-Type: text/plain\r\nContent-Length: " + body.length
                + "\r\nConnection: close\r\n\r\n";
        out.write(head.getBytes(StandardCharsets.US_ASCII));
        out.write(body);
        out.flush();
    }

    static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream(16 * 1024);
        byte[] chunk = new byte[16 * 1024];
        int n;
        while ((n = in.read(chunk)) > 0) buf.write(chunk, 0, n);
        return buf.toByteArray();
    }

    private static String readLine(InputStream in) throws IOException {
        StringBuilder sb = new StringBuilder(80);
        int c = -1;
        while ((c = in.read()) != -1) {
            if (c == '\n') break;
            sb.append((char) c);
        }
        String s = sb.toString();
        if (s.endsWith("\r")) s = s.substring(0, s.length() - 1);
        return (c == -1 && s.isEmpty()) ? null : s;
    }

    private static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
    }
}
