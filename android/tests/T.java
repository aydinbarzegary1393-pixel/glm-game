import com.glmgame.fps.GameServer;
import com.glmgame.fps.UpdaterCore;

import com.sun.net.httpserver.HttpServer;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.InetSocketAddress;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Desktop-JVM test harness for the pure Java parts of the APK
 * (GameServer + UpdaterCore). Run: java -cp testbuild T
 */
public class T {

    static int fails = 0;
    static void check(String name, boolean ok) { check(name, ok, null); }
    static void check(String name, boolean ok, Object detail) {
        System.out.println((ok ? "PASS " : "FAIL ") + name + (detail != null ? " | " + detail : ""));
        if (!ok) fails++;
    }

    public static void main(String[] args) throws Exception {
        Path repo = Paths.get("/home/z/my-project/glm-game");

        // ---------- GameServer ----------
        GameServer.StreamSource src = new GameServer.StreamSource() {
            public InputStream open(String path) throws IOException {
                File f = repo.resolve(path).toFile();
                return f.isFile() ? new BufferedInputStream(new FileInputStream(f)) : null;
            }
        };
        GameServer gs = new GameServer(src, 18877);
        gs.start();
        int port = gs.getPort();
        String base = "http://127.0.0.1:" + port;

        byte[] html = get(base + "/fps-game.html");
        check("S1 html served", html != null && html.length > 100000 && new String(html, 0, 40, StandardCharsets.US_ASCII).startsWith("<!DOCTYPE"), html == null ? "null" : html.length);
        byte[] js = get(base + "/fps-game-assets/three.min.js");
        check("S2 js served + mime", js != null && js.length > 100000, js == null ? "null" : js.length);
        Resp miss = getR(base + "/nope.png");
        check("S3 404 missing", miss.code == 404, miss.code);
        Resp trav = getR(base + "/../etc/passwd");
        check("S4 traversal rejected", trav.code == 403 || trav.code == 404, trav.code);
        Resp trav2 = getR(base + "/%2e%2e/etc/passwd");
        check("S5 encoded traversal rejected", trav2.code == 403 || trav2.code == 404, trav2.code);
        byte[] withQ = get(base + "/fps-game.html?cachebust=123");
        check("S6 query string ok", withQ != null && withQ.length == html.length, withQ == null ? "null" : withQ.length);
        Resp root = getR(base + "/");
        check("S7 root -> fps-game.html", root.code == 200 && root.body.length == html.length, root.code);
        Resp mime = getR(base + "/fps-game-assets/bg_menu.png");
        check("S8 png mime", mime.code == 200 && mime.ctype.contains("image/png"), mime.ctype);
        gs.stop();

        // ---------- UpdaterCore: semver ----------
        check("V1 1.10.0 > 1.9.0", UpdaterCore.isNewer("v1.10.0", "v1.9.0"));
        check("V2 1.9.0 !> 1.10.0", !UpdaterCore.isNewer("v1.9.0", "v1.10.0"));
        check("V3 equal", !UpdaterCore.isNewer("v1.9.0", "v1.9.0"));
        check("V4 garbage", !UpdaterCore.isNewer("banana", "v1.0.0") && !UpdaterCore.isNewer("v1.2.3", null));
        check("V5 patch", UpdaterCore.isNewer("v1.9.1", "v1.9.0"));

        // ---------- UpdaterCore: real manifest parse ----------
        String realManifest = new String(Files.readAllBytes(repo.resolve("version.json")), StandardCharsets.UTF_8);
        String[][] files = UpdaterCore.extractFiles(realManifest);
        check("M1 parse real manifest", files.length >= 20, files.length);
        check("M2 version", "v1.9.0".equals(UpdaterCore.extractString(realManifest, "version")), UpdaterCore.extractString(realManifest, "version"));
        boolean hashOk = true;
        for (String[] f : files) hashOk &= f[1].length() == 64;
        check("M3 hashes 64-hex", hashOk);

        // ---------- UpdaterCore.applyUpdate against a fake remote ----------
        Path remote = Files.createTempDirectory("glm-remote");
        Path local  = Files.createTempDirectory("glm-local");
        // remote serves: a.json (changed), b.js (same as local), c.png (new)
        byte[] aNew = "AAAA-v2".getBytes(); byte[] bSame = "BBBB".getBytes(); byte[] cNew = new byte[5000];
        new java.security.SecureRandom().nextBytes(cNew);
        Files.write(remote.resolve("a.json"), aNew);
        Files.write(remote.resolve("b.js"), bSame);
        Files.write(remote.resolve("c.png"), cNew);
        String mf = "{\"version\":\"v2.0.0\",\"entry\":\"x\",\"files\":["
                + ent("a.json", aNew) + "," + ent("b.js", bSame) + "," + ent("c.png", cNew) + "]}";
        // local already has b.js correct + a.json stale
        Files.write(local.resolve("a.json"), "AAAA-old".getBytes());
        Files.write(local.resolve("b.js"), bSame);

        HttpServer hs = HttpServer.create(new InetSocketAddress("127.0.0.1", 18999), 0);
        final AtomicInteger hits = new AtomicInteger();
        hs.createContext("/", ex -> {
            hits.incrementAndGet();
            Path p = remote.resolve(ex.getRequestURI().getPath().substring(1));
            byte[] body = Files.exists(p) ? Files.readAllBytes(p) : "404".getBytes();
            ex.sendResponseHeaders(Files.exists(p) ? 200 : 404, body.length);
            ex.getResponseBody().write(body);
            ex.close();
        });
        hs.start();

        UpdaterCore.Logger log = new UpdaterCore.Logger() {
            public void stage(String fa, String en) { }
            public void progress(int p) { }
        };
        AtomicInteger downloaded = new AtomicInteger();
        UpdaterCore.Logger counting = new UpdaterCore.Logger() {
            public void stage(String fa, String en) { }
            public void progress(int p) { }
        };
        UpdaterCore.Fetcher fetcher = url -> {
            HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
            int code = c.getResponseCode();
            InputStream in = code < 300 ? c.getInputStream() : c.getErrorStream();
            ByteArrayOutputStream buf = new ByteArrayOutputStream();
            byte[] ch = new byte[4096]; int n;
            while ((n = in.read(ch)) > 0) buf.write(ch, 0, n);
            c.disconnect();
            if (code >= 300) throw new IOException("HTTP " + code);
            return buf.toByteArray();
        };

        int hitsBefore = hits.get();
        boolean ok = UpdaterCore.applyUpdate(mf, "http://127.0.0.1:18999/", local.toFile(), fetcher, counting);
        check("U1 applyUpdate ok", ok);
        check("U2 only changed downloaded", hits.get() - hitsBefore == 2, hits.get() - hitsBefore); // a.json + c.png (b.js skipped)
        check("U3 a.json updated", Files.readAllBytes(local.resolve("a.json"))  == null || new String(Files.readAllBytes(local.resolve("a.json"))).equals("AAAA-v2"));
        check("U4 c.png new", Files.readAllBytes(local.resolve("c.png")).length == 5000);
        check("U5 version.json written", UpdaterCore.extractString(new String(Files.readAllBytes(local.resolve("version.json"))), "version").equals("v2.0.0"));

        // idempotent re-run: nothing to do
        hitsBefore = hits.get();
        boolean ok2 = UpdaterCore.applyUpdate(mf, "http://127.0.0.1:18999/", local.toFile(), fetcher, counting);
        check("U6 re-run no downloads", ok2 && hits.get() - hitsBefore == 0, hits.get() - hitsBefore);

        // corrupted download -> abort, old version intact
        hs.stop(0);
        String mfBad = "{\"version\":\"v3.0.0\",\"files\":[" + ent("a.json", "TAMPERED".getBytes()) + "]}";
        Files.write(remote.resolve("a.json"), "REAL-CONTENT".getBytes()); // remote serves different bytes than manifest claims
        HttpServer hs2 = HttpServer.create(new InetSocketAddress("127.0.0.1", 18998), 0);
        hs2.createContext("/", ex -> {
            Path p = remote.resolve(ex.getRequestURI().getPath().substring(1));
            byte[] body = Files.readAllBytes(p);
            ex.sendResponseHeaders(200, body.length);
            ex.getResponseBody().write(body);
            ex.close();
        });
        hs2.start();
        boolean ok3 = UpdaterCore.applyUpdate(mfBad, "http://127.0.0.1:18998/", local.toFile(), fetcher, counting);
        check("U7 hash mismatch aborts", !ok3);
        check("U8 old version intact", new String(Files.readAllBytes(local.resolve("a.json"))).equals("AAAA-v2"));
        check("U9 no version bump", new String(Files.readAllBytes(local.resolve("version.json"))).contains("v2.0.0"));
        hs2.stop(0);

        System.out.println(fails == 0 ? "\n==== ALL PASS ====" : "\n==== " + fails + " FAILURES ====");
        System.exit(fails == 0 ? 0 : 1);
    }

    static String ent(String path, byte[] data) throws Exception {
        java.security.MessageDigest md = java.security.MessageDigest.getInstance("SHA-256");
        StringBuilder sb = new StringBuilder();
        for (byte b : md.digest(data)) sb.append(String.format("%02x", b));
        return "{\"path\":\"" + path + "\",\"sha256\":\"" + sb + "\",\"size\":" + data.length + "}";
    }

    static byte[] get(String url) { try { return getR(url).body; } catch (Exception e) { return null; } }

    static Resp getR(String url) throws IOException {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(3000); c.setReadTimeout(5000);
        Resp r = new Resp();
        r.code = c.getResponseCode();
        r.ctype = c.getContentType() == null ? "" : c.getContentType();
        InputStream in = r.code < 300 ? c.getInputStream() : c.getErrorStream();
        if (in != null) r.body = T.readAll(in);
        c.disconnect();
        return r;
    }

    static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream b = new ByteArrayOutputStream();
        byte[] ch = new byte[8192]; int n;
        while ((n = in.read(ch)) > 0) b.write(ch, 0, n);
        return b.toByteArray();
    }

    static class Resp { int code; String ctype; byte[] body; }
}
